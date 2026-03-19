<<<<<<< Updated upstream
"""Knowledge Map Agent

Connects to the K8s Expertise MCP server to analyze GitHub repositories
and find domain experts based on git commit history. Deployed to AWS
Bedrock AgentCore Runtime.
"""

import os
import json
import boto3
import httpx
from typing import Dict, Any
from requests_aws4auth import AWS4Auth
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from strands.telemetry import StrandsTelemetry

from bedrock_agentcore.runtime import BedrockAgentCoreApp

StrandsTelemetry()

app = BedrockAgentCoreApp()

REGION = os.environ.get("AWS_REGION", "us-west-2")

ssm = boto3.client("ssm", region_name=REGION)

mcp_server_url = ""
try:
    response = ssm.get_parameter(Name="k8s_expertise_mcp_server_url")
    mcp_server_url = response["Parameter"]["Value"]
    print("MCP Server URL:", mcp_server_url)
except Exception as e:
    print(f"MCP Server URL not configured: {e}")
    print("Agent will not have access to expertise tools")


class SigV4Auth(httpx.Auth):
    """HTTPX Auth adapter for AWS SigV4 signing."""

    def __init__(self, service: str, region: str):
        session = boto3.Session()
        credentials = session.get_credentials()
        self.auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            service,
            session_token=credentials.token,
        )

    def auth_flow(self, request):
        import requests

        req = requests.Request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            data=request.content,
        ).prepare()
        self.auth(req)
        request.headers.update(req.headers)
        yield request


# Initialize MCP client factory (don't open connection at startup)
def get_mcp_client():
    """Create a fresh MCP client for each invocation."""
    if not mcp_server_url:
        return None
    try:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        return MCPClient(
            lambda: streamablehttp_client(
                url=mcp_server_url,
                headers=headers,
                auth=SigV4Auth("bedrock-agentcore", REGION),
                timeout=300.0,
            )
        )
    except Exception as e:
        print(f"Failed to create MCP client: {e}")
        return None

print("MCP client factory configured")

model = BedrockModel(
    model_id=os.environ.get(
        "AGENT_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    ),
    region_name=REGION,
)


@app.entrypoint
def agent_handler(payload: Dict[str, Any]):
    """Main handler for the Expert Finder Agent."""
    user_input = payload.get("prompt", "")
    print(f"Processing: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")

    SYSTEM_PROMPT = """You are a Knowledge Map Agent. You help developers and engineers find \
the right person to consult about Kubernetes issues based on git commit history analysis \
from the kubernetes/kubernetes GitHub repository.

Your workflow:
1. If the repository hasn't been analyzed yet, call analyze_repository("kubernetes", "kubernetes") first. \
   This takes 2-3 minutes on the first run (subsequent calls use cached results).
2. When a user describes a problem, call list_domains() to see the available knowledge domains.
3. Match the user's problem to the most relevant domain.
4. Call get_domain_experts(domain_name) with the matching domain name to find top contributors.
5. Present the experts with context on WHY they are qualified.

When presenting experts, always include:
- Their name and GitHub login
- Their expertise score (higher = more expertise in that domain)
- Number of commits in that domain
- Lines of code contributed (added + deleted)
- Examples of their recent work (sample commits)
- Which files they primarily work on

You can also look up specific contributors using get_contributor_profile(name) \
to see their expertise across all domains.

The 3 knowledge domains are identified automatically from the repository's \
commit history and file structure using AI analysis.

Important: Domain names must be used exactly as returned by list_domains(). \
Do not guess or modify domain names."""

    try:
        # Create a fresh MCP client for this invocation
        mcp_client = get_mcp_client()
        
        if mcp_client:
            with mcp_client:
                # Get tools inside the MCP context so they have access to the active session
                tools = mcp_client.list_tools_sync()
                print(f"Loaded {len(tools)} MCP tools in active session")
                
                # Create Agent inside the MCP context with fresh tools
                agent = Agent(
                    model=model,
                    tools=tools,
                    system_prompt=SYSTEM_PROMPT,
                )
                response = agent(user_input)
        else:
            # No MCP client available, create agent without tools
            agent = Agent(
                model=model,
                tools=[],
                system_prompt=SYSTEM_PROMPT,
            )
            response = agent(user_input)

        response_text = response.message["content"][0]["text"]
        print("Agent response generated successfully")
        return response_text

    except Exception as error:
        print(f"Error in agent invocation: {error}")
        import traceback
        traceback.print_exc()
        return f"I encountered an error: {str(error)}. Please try again."


if __name__ == "__main__":
    app.run()
=======
"""Knowledge Map Agent

Connects to the K8s Expertise MCP server to analyze GitHub repositories
and find domain experts based on git commit history. Deployed to AWS
Bedrock AgentCore Runtime.
"""

import os
import json
import boto3
import httpx
from typing import Dict, Any
from requests_aws4auth import AWS4Auth
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from strands.telemetry import StrandsTelemetry

from bedrock_agentcore.runtime import BedrockAgentCoreApp

StrandsTelemetry()

app = BedrockAgentCoreApp()

REGION = os.environ.get("AWS_REGION", "us-west-2")

ssm = boto3.client("ssm", region_name=REGION)

mcp_server_url = ""
try:
    response = ssm.get_parameter(Name="k8s_expertise_mcp_server_url")
    mcp_server_url = response["Parameter"]["Value"]
    print("MCP Server URL:", mcp_server_url)
except Exception as e:
    print(f"MCP Server URL not configured: {e}")
    print("Agent will not have access to expertise tools")


class SigV4Auth(httpx.Auth):
    """HTTPX Auth adapter for AWS SigV4 signing."""

    def __init__(self, service: str, region: str):
        session = boto3.Session()
        credentials = session.get_credentials()
        self.auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            service,
            session_token=credentials.token,
        )

    def auth_flow(self, request):
        import requests

        req = requests.Request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            data=request.content,
        ).prepare()
        self.auth(req)
        request.headers.update(req.headers)
        yield request


expertise_mcp_client = None
if mcp_server_url:
    try:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        expertise_mcp_client = MCPClient(
            lambda: streamablehttp_client(
                url=mcp_server_url,
                headers=headers,
                auth=SigV4Auth("bedrock-agentcore", REGION),
                timeout=300.0,
            )
        )
        print("MCP client initialized for expertise analysis")
    except Exception as e:
        print(f"Failed to initialize MCP client: {e}")
        expertise_mcp_client = None

model = BedrockModel(
    model_id=os.environ.get(
        "AGENT_MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    ),
    region_name=REGION,
)

agent = None

SYSTEM_PROMPT = """You are a Knowledge Map Agent. You help developers and engineers find \
the right person to consult about Kubernetes issues based on git commit history analysis \
from the kubernetes/kubernetes GitHub repository.

Your workflow:
1. If the repository hasn't been analyzed yet, call analyze_repository("kubernetes", "kubernetes") first. \
   This takes 2-3 minutes on the first run (subsequent calls use cached results).
2. When a user describes a problem, call list_domains() to see the available knowledge domains.
3. Match the user's problem to the most relevant domain.
4. Call get_domain_experts(domain_name) with the matching domain name to find top contributors.
5. Present the experts with context on WHY they are qualified.

When presenting experts, always include:
- Their name and GitHub login
- Their expertise score (higher = more expertise in that domain)
- Number of commits in that domain
- Lines of code contributed (added + deleted)
- Examples of their recent work (sample commits)
- Which files they primarily work on

You can also look up specific contributors using get_contributor_profile(name) \
to see their expertise across all domains.

The 3 knowledge domains are identified automatically from the repository's \
commit history and file structure using AI analysis.

Important: Domain names must be used exactly as returned by list_domains(). \
Do not guess or modify domain names."""

print("Agent model and system prompt configured")


@app.entrypoint
def agent_handler(payload: Dict[str, Any]):
    """Main handler for the Expert Finder Agent."""
    global agent

    user_input = payload.get("prompt", "")
    print(f"Processing: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")

    try:
        if agent is None and expertise_mcp_client:
            print("Initializing agent with MCP tools (single session)")
            with expertise_mcp_client:
                mcp_tools = expertise_mcp_client.list_tools_sync()
                print(f"Added {len(mcp_tools)} MCP tools")

                agent = Agent(
                    model=model,
                    tools=list(mcp_tools),
                    system_prompt=SYSTEM_PROMPT,
                )
                print(f"Agent initialized with {len(mcp_tools)} tool(s)")
                response = agent(user_input)

        elif agent is None:
            print("Initializing agent without MCP tools")
            agent = Agent(
                model=model,
                tools=[],
                system_prompt=SYSTEM_PROMPT,
            )
            response = agent(user_input)

        elif expertise_mcp_client:
            print("Using existing agent instance with memory context")
            with expertise_mcp_client:
                response = agent(user_input)

        else:
            print("Using existing agent instance (no MCP)")
            response = agent(user_input)

        response_text = response.message["content"][0]["text"]
        print("Agent response generated successfully")
        return response_text

    except Exception as error:
        print(f"Error in agent invocation: {error}")
        import traceback
        traceback.print_exc()
        return f"I encountered an error: {str(error)}. Please try again."


if __name__ == "__main__":
    app.run()
>>>>>>> Stashed changes
