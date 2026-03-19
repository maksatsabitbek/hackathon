"""Strands Agent for telecom network operations

This agent coordinates incident response by:
1. Detecting anomalies via MCP server
2. Retrieving resolutions from Knowledge Base of runbooks
"""

import os
import json
import boto3
import httpx
from typing import List, Dict, Any
from requests_aws4auth import AWS4Auth
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import retrieve
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore.runtime import BedrockAgentCoreApp
# Initialize the app
app = BedrockAgentCoreApp()


# Initialize Bedrock client for Knowledge Base queries
bedrock_client = boto3.client(
    "bedrock-agent-runtime",
    region_name=os.environ.get("AWS_REGION", "us-west-2")
)

# Get Knowledge Base ID and MCP Server URL from SSM Parameter Store
ssm = boto3.client('ssm', region_name=os.environ.get("AWS_REGION", "us-west-2"))

# Get Knowledge Base ID
kb_id = ''
try:
    response = ssm.get_parameter(Name='telco_anomaly_resolution_runbooks_kb')
    kb_id = response['Parameter']['Value']
    print("kb_id :", kb_id)
except Exception:
    print("Knowledge Base not configured. Standard resolution procedures:\n\n1. Verify power and connectivity\n2. Check component logs\n3. Escalate to NOC L2 if issue persists\n4. Follow standard incident response protocol")

os.environ["KNOWLEDGE_BASE_ID"] = kb_id

# Get MCP Server URL
mcp_server_url = ''
try:
    response = ssm.get_parameter(Name='telco_anomaly_detection_mcp_server_url')
    mcp_server_url = response['Parameter']['Value']
    print("MCP Server URL:", mcp_server_url)
except Exception as e:
    print(f"⚠️ MCP Server URL not configured: {e}")
    print("Agent will run with retrieve tool only")


# Utility to create SigV4 authorization needed for IAM role based MCP/Agent access
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
            session_token=credentials.token
        )

    def auth_flow(self, request):
        """Sign each request with SigV4."""
        import requests

        # Convert httpx request to requests PreparedRequest for signing
        req = requests.Request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            data=request.content
        ).prepare()

        # Apply SigV4 signature
        self.auth(req)

        # Copy signed headers back to httpx request
        request.headers.update(req.headers)

        yield request


# Initialize MCP client for anomaly detection
anomaly_detection_client = None
if mcp_server_url:
    try:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json"
        }
        anomaly_detection_client = MCPClient(lambda:
            streamablehttp_client(
                url=mcp_server_url,
                headers=headers,
                auth=SigV4Auth("bedrock-agentcore", "us-west-2"),
                timeout=30.0
            )
        )
        print("✅ MCP client initialized for anomaly detection")
    except Exception as e:
        print(f"❌ Failed to initialize MCP client: {e}")
        anomaly_detection_client = None

# Initialize the agent model in global scope
# Using Haiku 4.5 global inference profile for faster responses
model = BedrockModel(
    model_id=os.environ.get("AGENT_MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0"),
    region_name=os.environ.get("AWS_REGION", "us-west-2")
)

# global agent instance for conversation memory persistence
agent = None

# System prompt for the agent
SYSTEM_PROMPT = """You are a Telecom Network Operations Agent responsible for maintaining service quality across a Tier-1 telecom operator's network.

Your responsibilities:
1. **Anomaly Detection**: Monitor and detect network anomalies across different markets using MCP tools
2. **Impact Analysis**: Assess the business and customer impact of incidents
3. **Resolution Coordination**: Retrieve and apply resolution procedures from the knowledge base

When handling an incident, follow this workflow:
1. Use MCP tools to detect anomalies in the specified market
2. Analyze the impact for prioritization
3. For each critical anomaly, retrieve resolution procedures from the knowledge base using the retrieve tool

Response Guidelines:
- Be concise and action-oriented
- Always include severity level and customer impact
- Suggest escalation when appropriate

Market Coverage: Denver, Phoenix, Seattle, Portland, Las Vegas, Salt Lake City, San Francisco, Los Angeles, Dallas, Houston, Chicago, New York

Available Tools:
- MCP tools for anomaly detection and analysis (if MCP server is available)
- retrieve: Get resolution procedures from knowledge base for identified anomalies

Remember: Service quality and customer experience are paramount. Always make use of the internal resources for accurate actions and do not give generic recommendations not documented in the company documentation."""

print("Defined the model and system prompt")

# Agent initialization note:
# The agent is created on first invocation and reused for memory persistence.
# MCP client tools require active context managers, so the agent is invoked
# within the appropriate 'with client:' blocks.

@app.entrypoint

def agent_handler(payload: Dict[str, Any]):
    """Main handler for the Agent.

    Creates agent instance on first invocation with all available tools
    and reuses it for subsequent invocations to maintain conversation memory.

    Args:
        payload: Contains 'prompt' key with user input

    Returns:
        Plain text response from the agent
    """
    global agent

    # Extract user input from payload
    user_input = payload.get("prompt", "")
    # Debug: Log user input
    print(f"🔍 Processing user input: {user_input}")
    print("agent:", agent)
    
    try:
        # Create agent on first invocation for memory persistence
        if agent is None:
            print(f"🆕 Initializing agent with available tools")

            # Build tools list
            tools = [retrieve]
            
            # Add MCP client tools if available
            if anomaly_detection_client:
                try:
                    with anomaly_detection_client:
                        print("Retrieving tools from the MCP server")
                        mcp_tools = anomaly_detection_client.list_tools_sync()
                        tools.extend(mcp_tools)
                        print(f"✅ Added {len(mcp_tools)} MCP tools from anomaly_detection_client")
                except Exception as e:
                    print(f"⚠️ Failed to get tools from MCP client: {e}")

            # Create agent with all available tools (outside MCP context)
            agent = Agent(
                model=model,
                tools=tools,
                system_prompt=SYSTEM_PROMPT
            )
            print(f"✅ Agent initialized with {len(tools)} tool(s)")
        else:
            print(f"♻️ Using existing agent instance with memory context")

        # Generate response (works for both new and existing agent)
        if anomaly_detection_client:
            # Use MCP context for tool execution
            with anomaly_detection_client:
                response = agent(user_input)
        else:
            # No MCP tools, use agent directly
            response = agent(user_input)
            
        # Extract plain text response
        response_text = response.message['content'][0]['text']
        print(f"✅ Agent response generated successfully")

        # Return plain text (required by AgentCore Runtime)
        return response_text

    except Exception as error:
        print(f"❌ Error in agent invocation: {error}")
        import traceback
        traceback.print_exc()
        # Return error message as plain text
        return f"I apologize, but I encountered a technical error: {str(error)}. Please try again."


if __name__ == "__main__":
    app.run()