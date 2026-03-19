"""Knowledge Map -- Streamlit Dashboard

Interactive frontend for the Knowledge Map Agent.
Features:
  - Heatmap: contributors vs domains with color-coded expertise scores
  - Domain cards: 3 identified domains with top experts
  - Contributor profiles: search and view expertise across domains
  - Chat: ask questions and get dynamic visualizations
"""

import json
import uuid
import boto3
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from boto3.dynamodb.conditions import Key, Attr

REGION = "us-west-2"
TABLE_NAME = "k8s-expertise-map"

# ---------------------------------------------------------------------------
# AWS clients (cached)
# ---------------------------------------------------------------------------

@st.cache_resource
def get_dynamodb_table():
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    return dynamodb.Table(TABLE_NAME)


@st.cache_resource
def get_agent_client():
    return boto3.client("bedrock-agentcore", region_name=REGION)


@st.cache_resource
def get_agent_arn():
    ssm = boto3.client("ssm", region_name=REGION)
    try:
        resp = ssm.get_parameter(Name="K8sExpertFinderAgentArn")
        return resp["Parameter"]["Value"]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Data loading (cached for 5 minutes)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def load_domains():
    table = get_dynamodb_table()
    resp = table.scan(
        FilterExpression=Attr("sk").eq("METADATA") & Attr("pk").begins_with("DOMAIN#")
    )
    return resp.get("Items", [])


@st.cache_data(ttl=300)
def load_domain_experts(domain_name: str):
    table = get_dynamodb_table()
    resp = table.query(
        KeyConditionExpression=Key("pk").eq(f"DOMAIN#{domain_name}")
        & Key("sk").begins_with("CONTRIBUTOR#")
    )
    items = resp.get("Items", [])
    items.sort(key=lambda x: int(x.get("expertise_score", 0)), reverse=True)
    return items


@st.cache_data(ttl=300)
def load_all_experts():
    table = get_dynamodb_table()
    resp = table.scan(FilterExpression=Attr("sk").begins_with("CONTRIBUTOR#"))
    return resp.get("Items", [])


# ---------------------------------------------------------------------------
# Visualization helpers
# ---------------------------------------------------------------------------

def build_heatmap_data():
    """Build a DataFrame for the heatmap: contributors (rows) vs domains (cols)."""
    domains = load_domains()
    if not domains:
        return None

    rows = []
    for d in domains:
        domain_name = d["name"]
        experts = load_domain_experts(domain_name)
        for e in experts:
            rows.append({
                "Contributor": e.get("contributor_name", "Unknown"),
                "Domain": domain_name,
                "Score": int(e.get("expertise_score", 0)),
                "Commits": int(e.get("commit_count", 0)),
                "Lines Added": int(e.get("lines_added", 0)),
            })

    if not rows:
        return None
    return pd.DataFrame(rows)


def render_heatmap(df):
    pivot = df.pivot_table(
        index="Contributor", columns="Domain", values="Score", aggfunc="sum", fill_value=0
    )
    pivot = pivot.loc[pivot.sum(axis=1).nlargest(15).index]

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale="YlOrRd",
            text=pivot.values,
            texttemplate="%{text:,.0f}",
            textfont={"size": 11},
            hovertemplate="<b>%{y}</b><br>Domain: %{x}<br>Score: %{z:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Contributor Expertise Heatmap (Top 15)",
        xaxis_title="Knowledge Domain",
        yaxis_title="Contributor",
        height=max(400, len(pivot) * 35 + 100),
        yaxis={"autorange": "reversed"},
        margin=dict(l=200),
    )
    return fig


def render_domain_bar(df, domain_name):
    domain_df = df[df["Domain"] == domain_name].nlargest(10, "Score")
    fig = px.bar(
        domain_df,
        x="Score",
        y="Contributor",
        orientation="h",
        color="Score",
        color_continuous_scale="YlOrRd",
        title=f"Top Experts: {domain_name}",
    )
    fig.update_layout(
        yaxis={"autorange": "reversed"},
        height=max(300, len(domain_df) * 35 + 100),
        showlegend=False,
    )
    return fig


def render_contributor_radar(contributor_scores: dict, name: str):
    domains = list(contributor_scores.keys())
    scores = list(contributor_scores.values())
    domains.append(domains[0])
    scores.append(scores[0])

    fig = go.Figure(
        data=go.Scatterpolar(r=scores, theta=domains, fill="toself", name=name)
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title=f"Expertise Profile: {name}",
        height=400,
    )
    return fig


# ---------------------------------------------------------------------------
# Agent chat
# ---------------------------------------------------------------------------

def invoke_agent(prompt: str) -> str:
    agent_arn = get_agent_arn()
    if not agent_arn:
        return "Agent not deployed. Please deploy the agent first using deploy_agent.py"

    client = get_agent_client()
    session_id = st.session_state.get("agent_session_id")
    if not session_id:
        session_id = str(uuid.uuid4()) + "-" + str(uuid.uuid4())[:8]
        st.session_state["agent_session_id"] = session_id

    try:
        resp = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            runtimeSessionId=session_id,
            payload=json.dumps({"prompt": prompt}),
            qualifier="DEFAULT",
        )
        body = resp["response"].read()
        return json.loads(body) if isinstance(body, (bytes, str)) else str(body)
    except Exception as e:
        return f"Error calling agent: {str(e)}"


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Knowledge Map",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .domain-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5986 100%);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        color: white;
    }
    .domain-card h3 { margin: 0 0 8px 0; color: #7fdbff; }
    .domain-card p { margin: 0; opacity: 0.9; font-size: 14px; }
    .expert-badge {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        border-radius: 20px;
        padding: 4px 12px;
        margin: 4px 2px;
        font-size: 13px;
    }
    .score-big {
        font-size: 32px;
        font-weight: bold;
        color: #7fdbff;
    }
    .metric-label { font-size: 12px; opacity: 0.7; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔍 Knowledge Map")
st.caption("Find the right person to help with your Kubernetes issues -- powered by AI analysis of git commit history")

tab_dashboard, tab_chat, tab_profiles = st.tabs(["📊 Dashboard", "💬 Chat", "👤 Profiles"])


# ---- TAB 1: DASHBOARD ----
with tab_dashboard:
    domains = load_domains()

    if not domains:
        st.warning(
            "No analysis data found. Run the agent with: "
            "\"Analyze the kubernetes/kubernetes repository\" to populate the data."
        )
        st.stop()

    # Domain cards
    st.subheader("Knowledge Domains")
    cols = st.columns(len(domains))
    for i, d in enumerate(domains):
        experts = load_domain_experts(d["name"])
        with cols[i]:
            top_names = ", ".join(e.get("contributor_name", "?") for e in experts[:3])
            keywords = ", ".join(d.get("keywords", [])[:5])
            st.markdown(
                f"""
                <div class="domain-card">
                    <h3>{d['name']}</h3>
                    <p>{d.get('description', '')}</p>
                    <br/>
                    <div class="metric-label">TOP EXPERTS</div>
                    <div class="expert-badge">{top_names}</div>
                    <br/><br/>
                    <div class="metric-label">KEYWORDS</div>
                    <div class="expert-badge">{keywords}</div>
                    <br/><br/>
                    <div class="score-big">{len(experts)}</div>
                    <div class="metric-label">CONTRIBUTORS</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # Heatmap
    st.subheader("Expertise Heatmap")
    df = build_heatmap_data()
    if df is not None and not df.empty:
        fig = render_heatmap(df)
        st.plotly_chart(fig, use_container_width=True, key="heatmap_chart")

        # Per-domain bar charts
        st.subheader("Domain Breakdown")
        bar_cols = st.columns(len(domains))
        for i, d in enumerate(domains):
            with bar_cols[i]:
                bar_fig = render_domain_bar(df, d["name"])
                st.plotly_chart(bar_fig, use_container_width=True, key=f"domain_bar_{i}_{d['name']}")
    else:
        st.info("No expertise data available yet.")


# ---- TAB 2: CHAT ----
with tab_chat:
    st.subheader("Ask the Knowledge Map Agent")
    st.caption(
        "Ask questions like: \"Who can help me with scheduling issues?\" or "
        "\"I have a networking problem with kube-proxy, who should I contact?\""
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "chart" in msg:
                st.plotly_chart(msg["chart"], use_container_width=True)

    if prompt := st.chat_input("Describe your Kubernetes issue..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_text = invoke_agent(prompt)

            st.markdown(response_text)

            # Dynamic visualization: if the response mentions a domain, show its chart
            chart = None
            df = build_heatmap_data()
            if df is not None:
                domains = load_domains()
                for d in domains:
                    if d["name"].lower() in prompt.lower() or d["name"].lower() in str(response_text).lower():
                        chart = render_domain_bar(df, d["name"])
                        st.plotly_chart(chart, use_container_width=True, key=f"chat_chart_{len(st.session_state.messages)}")
                        break

            msg_data = {"role": "assistant", "content": response_text}
            if chart:
                msg_data["chart"] = chart
            st.session_state.messages.append(msg_data)


# ---- TAB 3: PROFILES ----
with tab_profiles:
    st.subheader("Contributor Profiles")

    all_experts = load_all_experts()
    unique_names = sorted({e.get("contributor_name", "") for e in all_experts if e.get("contributor_name")})

    if not unique_names:
        st.info("No contributor data available. Analyze a repository first.")
    else:
        selected = st.selectbox("Select a contributor", unique_names)

        if selected:
            matches = [
                e for e in all_experts
                if e.get("contributor_name") == selected
            ]

            if matches:
                # Summary metrics
                total_score = sum(int(m.get("expertise_score", 0)) for m in matches)
                total_commits = sum(int(m.get("commit_count", 0)) for m in matches)
                total_lines = sum(
                    int(m.get("lines_added", 0)) + int(m.get("lines_deleted", 0))
                    for m in matches
                )

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Expertise Score", f"{total_score:,}")
                m2.metric("Total Commits", f"{total_commits:,}")
                m3.metric("Total Lines Changed", f"{total_lines:,}")
                m4.metric("Active Domains", len(matches))

                # Radar chart
                contributor_scores = {
                    m.get("pk", "").replace("DOMAIN#", ""): int(m.get("expertise_score", 0))
                    for m in matches
                }
                if len(contributor_scores) >= 2:
                    radar = render_contributor_radar(contributor_scores, selected)
                    st.plotly_chart(radar, use_container_width=True, key=f"radar_{selected}")

                # Domain details
                st.divider()
                for m in sorted(matches, key=lambda x: int(x.get("expertise_score", 0)), reverse=True):
                    domain = m.get("pk", "").replace("DOMAIN#", "")
                    with st.expander(f"**{domain}** -- Score: {int(m.get('expertise_score', 0)):,}", expanded=True):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Commits", int(m.get("commit_count", 0)))
                        c2.metric("Lines Added", f"{int(m.get('lines_added', 0)):,}")
                        c3.metric("Lines Deleted", f"{int(m.get('lines_deleted', 0)):,}")

                        top_files = m.get("top_files", [])
                        if top_files:
                            st.markdown("**Top Files:**")
                            for f in top_files[:5]:
                                if isinstance(f, dict):
                                    st.code(f"{f.get('file', '')}  ({f.get('count', 0)} changes)")
                                else:
                                    st.code(str(f))

                        sample_commits = m.get("sample_commits", [])
                        if sample_commits:
                            st.markdown("**Recent Commits:**")
                            for sc in sample_commits:
                                st.markdown(f"- {sc}")
