"""MCP Server for Kubernetes Expertise Analysis.

Provides tools for analyzing GitHub repositories, identifying knowledge domains,
and finding domain experts based on git commit history. Connects live to GitHub API,
uses Bedrock Claude for domain identification, and caches results in DynamoDB.
"""

import os
import json
import time
import re
from datetime import datetime, timezone
from collections import defaultdict

import boto3
import requests
from boto3.dynamodb.conditions import Key, Attr
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(host="0.0.0.0", port=8000, stateless_http=True)

REGION = os.environ.get("AWS_REGION", "us-west-2")
TABLE_NAME = os.environ.get("EXPERTISE_TABLE", "k8s-expertise-map")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

ssm = boto3.client("ssm", region_name=REGION)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)

BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0"
)

GITHUB_TOKEN = ""
try:
    resp = ssm.get_parameter(Name="k8s_expertise_github_token", WithDecryption=True)
    GITHUB_TOKEN = resp["Parameter"]["Value"]
    print("GitHub token loaded from SSM")
except Exception as e:
    print(f"GitHub token not configured in SSM: {e}")

BOT_AUTHORS = {
    "k8s-ci-robot",
    "dependabot[bot]",
    "github-actions[bot]",
    "k8s-cherrypick-robot",
    "k8s-publishing-bot",
    "k8s-infra-cherrypick-robot",
    "fejta-bot",
    "k8s-triage-robot",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _github_headers():
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def _invoke_bedrock(prompt: str) -> str:
    response = bedrock_runtime.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }),
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def _fetch_commits(repo_owner: str, repo_name: str, max_commits: int = 1000):
    """Fetch commits from GitHub, filtering merge commits and bots."""
    commits = []
    page = 1
    per_page = 100

    while len(commits) < max_commits:
        resp = requests.get(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits",
            params={"per_page": per_page, "page": page},
            headers=_github_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        page_commits = resp.json()

        if not page_commits:
            break

        for c in page_commits:
            if len(c.get("parents", [])) > 1:
                continue

            author = c.get("author") or {}
            commit_data = c.get("commit", {})
            author_info = commit_data.get("author", {})
            author_login = author.get("login", "")
            author_name = author_info.get("name", author_login)
            author_email = author_info.get("email", "")

            if author_login in BOT_AUTHORS or author_name in BOT_AUTHORS:
                continue
            if "[bot]" in author_login or "bot@" in author_email:
                continue

            commits.append({
                "sha": c["sha"],
                "author_name": author_name,
                "author_email": author_email,
                "author_login": author_login,
                "message": commit_data.get("message", ""),
                "date": author_info.get("date", ""),
            })

            if len(commits) >= max_commits:
                break

        page += 1
        if page > 50:
            break
        time.sleep(0.3)

    return commits


def _fetch_commit_details(repo_owner, repo_name, commits, sample_size=200):
    """Fetch file-level stats for a sample of commits (prioritising contributor diversity)."""
    contributors = defaultdict(list)
    for c in commits:
        contributors[c["author_email"]].append(c)

    sampled_shas = set()
    for email, contributor_commits in contributors.items():
        for cc in contributor_commits[:5]:
            sampled_shas.add(cc["sha"])
            if len(sampled_shas) >= sample_size:
                break
        if len(sampled_shas) >= sample_size:
            break

    for c in commits:
        if len(sampled_shas) >= sample_size:
            break
        sampled_shas.add(c["sha"])

    commit_files = {}
    for sha in sampled_shas:
        try:
            resp = requests.get(
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{sha}",
                headers=_github_headers(),
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            commit_files[sha] = [
                {
                    "filename": f.get("filename", ""),
                    "additions": f.get("additions", 0),
                    "deletions": f.get("deletions", 0),
                    "status": f.get("status", ""),
                }
                for f in data.get("files", [])
            ]
            time.sleep(0.5)
        except Exception as e:
            print(f"Warning: failed to fetch details for {sha[:8]}: {e}")

    return commit_files


def _identify_domains(commits, commit_files):
    """Use Bedrock to identify the top 3 knowledge domains."""
    dir_counts = defaultdict(int)
    for files in commit_files.values():
        for f in files:
            parts = f["filename"].split("/")
            if len(parts) >= 2:
                dir_counts["/".join(parts[:2])] += 1
            if len(parts) >= 3:
                dir_counts["/".join(parts[:3])] += 1

    top_dirs = sorted(dir_counts.items(), key=lambda x: x[1], reverse=True)[:100]
    sample_messages = [c["message"].split("\n")[0] for c in commits[:200]]

    prompt = f"""Analyze this GitHub repository structure and commit messages to identify the TOP 3 main knowledge domain areas.

Top directory paths (with file change counts):
{json.dumps(top_dirs, indent=2)}

Sample recent commit messages (first line only):
{json.dumps(sample_messages[:100], indent=2)}

Return EXACTLY this JSON format (no markdown, no explanation, just the raw JSON array):
[
  {{
    "name": "Short Domain Name",
    "description": "One sentence description of what this domain covers",
    "path_patterns": ["dir/subdir", "other/path"],
    "keywords": ["keyword1", "keyword2", "keyword3"]
  }}
]

Rules:
- Return exactly 3 domains
- path_patterns: directory prefixes that match files belonging to this domain
- keywords: words commonly found in commit messages for this domain
- Domains should be distinct and non-overlapping"""

    response_text = _invoke_bedrock(prompt)

    try:
        match = re.search(r"\[.*\]", response_text, re.DOTALL)
        domains = json.loads(match.group()) if match else json.loads(response_text)
    except (json.JSONDecodeError, AttributeError):
        domains = [
            {"name": "API & Core Infrastructure", "description": "Core API server, resource types, and cluster infrastructure", "path_patterns": ["pkg/api", "staging/src", "cmd/kube-apiserver"], "keywords": ["api", "resource", "server", "client"]},
            {"name": "Scheduling & Node Management", "description": "Pod scheduling, kubelet, and node lifecycle", "path_patterns": ["pkg/scheduler", "pkg/kubelet", "cmd/kubelet"], "keywords": ["scheduler", "scheduling", "node", "kubelet"]},
            {"name": "Networking & Storage", "description": "Network policies, services, proxy, and persistent storage", "path_patterns": ["pkg/proxy", "pkg/volume", "pkg/controller"], "keywords": ["network", "service", "proxy", "volume", "storage"]},
        ]

    return domains[:3]


def _classify_impact(commits):
    """Use Bedrock to build an impact classifier, then apply it to all commits."""
    sample_messages = [c["message"].split("\n")[0] for c in commits[:100]]

    prompt = f"""Analyze these git commit messages and create keyword-based rules to classify commits into impact tiers.

Sample commit messages:
{json.dumps(sample_messages, indent=2)}

Return EXACTLY this JSON (no markdown, no explanation, just the raw JSON object):
{{
  "high": {{
    "keywords": ["keyword1", "keyword2"]
  }},
  "medium": {{
    "keywords": ["keyword1", "keyword2"]
  }},
  "low": {{
    "keywords": ["keyword1", "keyword2"]
  }}
}}

Rules:
- high: critical fixes, new features, security patches, performance optimizations
- medium: regular bug fixes, test additions, refactors
- low: typo fixes, comment updates, doc-only changes, auto-generated code
- keywords should be lowercase
- A commit not matching any rule defaults to medium"""

    response_text = _invoke_bedrock(prompt)

    try:
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        classifier = json.loads(match.group()) if match else json.loads(response_text)
    except (json.JSONDecodeError, AttributeError):
        classifier = {
            "high": {"keywords": ["security", "cve", "critical", "vulnerability", "crash", "performance", "feature"]},
            "medium": {"keywords": ["fix", "bug", "test", "refactor", "update", "add"]},
            "low": {"keywords": ["typo", "comment", "doc", "readme", "generated", "vendor", "cleanup"]},
        }

    impact_map = {}
    for c in commits:
        first_line = c["message"].split("\n")[0].lower()
        impact = "medium"

        for kw in classifier.get("high", {}).get("keywords", []):
            if kw.lower() in first_line:
                impact = "high"
                break

        if impact == "medium":
            for kw in classifier.get("low", {}).get("keywords", []):
                if kw.lower() in first_line:
                    impact = "low"
                    break

        impact_map[c["sha"]] = impact

    return impact_map


def _score_contributors(commits, commit_files, domains, impact_map):
    """Score each contributor per domain using file paths, keywords, and impact."""
    IMPACT_MULTIPLIERS = {"high": 3.0, "medium": 1.0, "low": 0.3}

    domain_scores = {d["name"]: {} for d in domains}

    for c in commits:
        sha = c["sha"]
        email = c["author_email"]
        impact = impact_map.get(sha, "medium")
        multiplier = IMPACT_MULTIPLIERS.get(impact, 1.0)
        first_line = c["message"].split("\n")[0]

        files = commit_files.get(sha, [])
        matched_domains = set()

        for f in files:
            for d in domains:
                for pattern in d.get("path_patterns", []):
                    if f["filename"].startswith(pattern) or pattern in f["filename"]:
                        matched_domains.add(d["name"])

        msg_lower = c["message"].lower()
        for d in domains:
            for kw in d.get("keywords", []):
                if kw.lower() in msg_lower:
                    matched_domains.add(d["name"])

        if not matched_domains:
            matched_domains = {d["name"] for d in domains}
            multiplier *= 0.1

        total_added = sum(f.get("additions", 0) for f in files)
        total_deleted = sum(f.get("deletions", 0) for f in files)
        if not files:
            total_added, total_deleted = 10, 5

        for domain_name in matched_domains:
            if email not in domain_scores[domain_name]:
                domain_scores[domain_name][email] = {
                    "score": 0.0,
                    "commit_count": 0,
                    "lines_added": 0,
                    "lines_deleted": 0,
                    "files": {},
                    "messages": [],
                    "author_name": c["author_name"],
                    "author_login": c.get("author_login", ""),
                }

            entry = domain_scores[domain_name][email]
            entry["author_name"] = c["author_name"]
            entry["author_login"] = c.get("author_login", "")
            entry["commit_count"] += 1
            entry["lines_added"] += total_added
            entry["lines_deleted"] += total_deleted
            entry["score"] += (total_added * 1.0 + total_deleted * 0.5) * multiplier

            for f in files:
                fname = f["filename"]
                entry["files"][fname] = entry["files"].get(fname, 0) + 1

            if len(entry["messages"]) < 5:
                entry["messages"].append(first_line[:200])

    return domain_scores


def _store_results(repo_owner, repo_name, domains, domain_scores):
    """Persist analysis results to DynamoDB."""
    repo_key = f"{repo_owner}/{repo_name}"

    table.put_item(Item={
        "pk": f"REPO#{repo_key}",
        "sk": "METADATA",
        "last_analyzed": datetime.now(timezone.utc).isoformat(),
        "total_domains": len(domains),
        "domain_names": [d["name"] for d in domains],
    })

    for d in domains:
        domain_name = d["name"]
        domain_pk = f"DOMAIN#{domain_name}"

        table.put_item(Item={
            "pk": domain_pk,
            "sk": "METADATA",
            "name": domain_name,
            "description": d.get("description", ""),
            "path_patterns": d.get("path_patterns", []),
            "keywords": d.get("keywords", []),
            "repo": repo_key,
        })

        contributors = domain_scores.get(domain_name, {})
        sorted_contribs = sorted(
            contributors.items(), key=lambda x: x[1]["score"], reverse=True
        )[:20]

        for email, data in sorted_contribs:
            top_files = sorted(
                data["files"].items(), key=lambda x: x[1], reverse=True
            )[:10]

            table.put_item(Item={
                "pk": domain_pk,
                "sk": f"CONTRIBUTOR#{email}",
                "contributor_name": data["author_name"],
                "contributor_login": data.get("author_login", ""),
                "contributor_email": email,
                "expertise_score": int(data["score"]),
                "commit_count": data["commit_count"],
                "lines_added": data["lines_added"],
                "lines_deleted": data["lines_deleted"],
                "top_files": [{"file": f, "count": c} for f, c in top_files],
                "sample_commits": data["messages"][:5],
                "repo": repo_key,
            })


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def analyze_repository(repo_owner: str, repo_name: str) -> str:
    """Analyze a GitHub repository to identify knowledge domains and map contributors.

    Fetches the last 1000 commits (filtering bots and merges), uses AI to identify
    the top 3 knowledge domains, scores contributors by impact-weighted expertise,
    and caches results in DynamoDB for fast subsequent queries.

    Args:
        repo_owner: GitHub repository owner (e.g. 'kubernetes')
        repo_name: GitHub repository name (e.g. 'kubernetes')

    Returns:
        JSON summary with domains and top contributors per domain
    """
    try:
        repo_key = f"{repo_owner}/{repo_name}"

        try:
            cached = table.get_item(Key={"pk": f"REPO#{repo_key}", "sk": "METADATA"})
            if "Item" in cached:
                last_analyzed = cached["Item"].get("last_analyzed", "")
                if last_analyzed:
                    analyzed_time = datetime.fromisoformat(last_analyzed)
                    age_hours = (datetime.now(timezone.utc) - analyzed_time).total_seconds() / 3600
                    if age_hours < 24:
                        return json.dumps({
                            "status": "cached",
                            "message": f"Repository analyzed {age_hours:.1f}h ago. Use list_domains / get_domain_experts to query.",
                            "repo": repo_key,
                            "domains": cached["Item"].get("domain_names", []),
                        })
        except Exception:
            pass

        print(f"[1/6] Fetching commits from {repo_key}...")
        commits = _fetch_commits(repo_owner, repo_name, max_commits=1000)
        print(f"[2/6] Fetched {len(commits)} human commits")

        print("[3/6] Fetching file-level details for sampled commits...")
        commit_files = _fetch_commit_details(repo_owner, repo_name, commits, sample_size=200)
        print(f"       Got details for {len(commit_files)} commits")

        print("[4/6] Identifying knowledge domains via Bedrock...")
        domains = _identify_domains(commits, commit_files)
        print(f"       Domains: {[d['name'] for d in domains]}")

        print("[5/6] Classifying commit impact via Bedrock...")
        impact_map = _classify_impact(commits)

        print("[6/6] Scoring contributors and storing results...")
        domain_scores = _score_contributors(commits, commit_files, domains, impact_map)
        _store_results(repo_owner, repo_name, domains, domain_scores)

        summary = {
            "status": "success",
            "repo": repo_key,
            "total_commits_analyzed": len(commits),
            "commits_with_file_details": len(commit_files),
            "domains": [],
        }

        for d in domains:
            domain_name = d["name"]
            contributors = domain_scores.get(domain_name, {})
            top_3 = sorted(contributors.items(), key=lambda x: x[1]["score"], reverse=True)[:3]
            summary["domains"].append({
                "name": domain_name,
                "description": d.get("description", ""),
                "total_contributors": len(contributors),
                "top_contributors": [
                    {"name": data["author_name"], "email": email, "score": int(data["score"]), "commits": data["commit_count"]}
                    for email, data in top_3
                ],
            })

        return json.dumps(summary, default=str)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"status": "error", "message": f"Analysis failed: {str(e)}"})


@mcp.tool()
def list_domains() -> str:
    """List all identified knowledge domains from the analyzed repository.

    Returns:
        JSON with domain names, descriptions, path patterns, and keywords
    """
    try:
        response = table.scan(
            FilterExpression=Attr("sk").eq("METADATA") & Attr("pk").begins_with("DOMAIN#")
        )
        items = response.get("Items", [])

        if not items:
            return json.dumps({
                "status": "success",
                "message": "No domains found. Run analyze_repository first.",
                "domains": [],
            })

        domains = [
            {
                "name": item.get("name", ""),
                "description": item.get("description", ""),
                "path_patterns": item.get("path_patterns", []),
                "keywords": item.get("keywords", []),
            }
            for item in items
        ]

        return json.dumps({"status": "success", "domain_count": len(domains), "domains": domains})

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to list domains: {str(e)}"})


@mcp.tool()
def get_domain_experts(domain_name: str) -> str:
    """Get the top contributors / experts for a specific knowledge domain.

    Args:
        domain_name: Exact domain name as returned by list_domains

    Returns:
        JSON with ranked list of experts including scores and commit details
    """
    try:
        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"DOMAIN#{domain_name}") & Key("sk").begins_with("CONTRIBUTOR#")
        )
        items = response.get("Items", [])

        if not items:
            return json.dumps({
                "status": "success",
                "domain": domain_name,
                "message": f"No experts found for domain '{domain_name}'",
                "experts": [],
            })

        items.sort(key=lambda x: int(x.get("expertise_score", 0)), reverse=True)

        experts = [
            {
                "name": item.get("contributor_name", ""),
                "email": item.get("contributor_email", ""),
                "login": item.get("contributor_login", ""),
                "expertise_score": int(item.get("expertise_score", 0)),
                "commit_count": int(item.get("commit_count", 0)),
                "lines_added": int(item.get("lines_added", 0)),
                "lines_deleted": int(item.get("lines_deleted", 0)),
                "top_files": item.get("top_files", []),
                "sample_commits": item.get("sample_commits", []),
            }
            for item in items
        ]

        return json.dumps({
            "status": "success",
            "domain": domain_name,
            "expert_count": len(experts),
            "experts": experts,
        }, default=str)

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to get experts: {str(e)}"})


@mcp.tool()
def get_contributor_profile(contributor_name: str) -> str:
    """Look up a specific contributor's expertise across all domains.

    Args:
        contributor_name: The contributor's name, email, or GitHub login

    Returns:
        JSON with the contributor's expertise profile in each domain
    """
    try:
        search_term = contributor_name.lower()

        response = table.scan(
            FilterExpression=Attr("sk").begins_with("CONTRIBUTOR#")
        )
        items = response.get("Items", [])

        matching = []
        for item in items:
            name = item.get("contributor_name", "").lower()
            email = item.get("contributor_email", "").lower()
            login = item.get("contributor_login", "").lower()

            if search_term in name or search_term in email or search_term in login:
                domain = item.get("pk", "").replace("DOMAIN#", "")
                matching.append({
                    "domain": domain,
                    "name": item.get("contributor_name", ""),
                    "email": item.get("contributor_email", ""),
                    "login": item.get("contributor_login", ""),
                    "expertise_score": int(item.get("expertise_score", 0)),
                    "commit_count": int(item.get("commit_count", 0)),
                    "lines_added": int(item.get("lines_added", 0)),
                    "lines_deleted": int(item.get("lines_deleted", 0)),
                    "top_files": item.get("top_files", []),
                    "sample_commits": item.get("sample_commits", []),
                })

        if not matching:
            return json.dumps({
                "status": "success",
                "message": f"No contributor found matching '{contributor_name}'",
                "profiles": [],
            })

        return json.dumps({
            "status": "success",
            "contributor": contributor_name,
            "domain_count": len(matching),
            "profiles": matching,
        }, default=str)

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to get profile: {str(e)}"})


if __name__ == "__main__":
    print("Starting K8s Expertise MCP Server on port 8000...")
    print("Available tools:")
    print("  - analyze_repository(repo_owner, repo_name)")
    print("  - list_domains()")
    print("  - get_domain_experts(domain_name)")
    print("  - get_contributor_profile(contributor_name)")
    mcp.run(transport="streamable-http")
