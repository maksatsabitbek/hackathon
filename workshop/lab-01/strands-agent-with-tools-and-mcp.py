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

# TODO-1: Import strands agent and MCP related packages


# Initialize Bedrock client for Knowledge Base queries
bedrock_client = boto3.client(
    "bedrock-agent-runtime",
    region_name=os.environ.get("AWS_REGION", "us-west-2")
)

# Initialize SSM Client to read parameters from SSM Parameter Store
ssm = boto3.client('ssm', region_name=os.environ.get("AWS_REGION", "us-west-2"))

# Get Knowledge Base ID from SSM Parameter Store
kb_id = ''
try:
    
    # TODO-2: Add code to read the SSM Parameter for knowledgebase ID
    
    kb_id = response['Parameter']['Value']
    print("kb_id :", kb_id)
except Exception:
    print("Knowledge Base not configured. Standard resolution procedures:\n\n1. Verify power and connectivity\n2. Check component logs\n3. Escalate to NOC L2 if issue persists\n4. Follow standard incident response protocol")

os.environ["KNOWLEDGE_BASE_ID"] = kb_id

# Get MCP Server URL from SSM Parameter Store
mcp_server_url = ''
try:

    # TODO-3: Add code to read the SSM Parameter for MCP server URL
    
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
        
        #TODO-4: Add code snippet to create MCP client for the anomaly detection MCP server.

        print("✅ MCP client initialized for anomaly detection")
    except Exception as e:
        print(f"❌ Failed to initialize MCP client: {e}")
        anomaly_detection_client = None

# Initialize the agent model in global scope. Using Haiku 4.5 global inference profile for faster responses

#TODO-5: Create model object with the choice of model provider you like to use. For this workshop, we will be using Amazon Bedrock hosted Anthropic Claude Haiku 4.5 model.


# global agent instance for conversation memory persistence
agent = None

# System prompt for the agent

#TODO-6: Add the system prompt to provide instructions to your agent


# Agent initialization note:
# The agent is created on first invocation and reused for memory persistence.
# MCP client tools require active context managers, so the agent is invoked
# within the appropriate 'with client:' blocks.

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
    print(f"🔍 Processing: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")
    response_text = ''
    try:
        # Create agent on first invocation for memory persistence
        if agent is None:
            print(f"🆕 Initializing agent with available tools")

            # Build tools list            
            #TODO-7: Create a tool list with retrieve tool
            
            if anomaly_detection_client:
                try:
                    # Add MCP client tools if available
                    with anomaly_detection_client:
                        
                        #TODO-8: Extend the tool list with the tools supported by anomaly detection MCP server.

                        print(f"✅ Added {len(mcp_tools)} MCP tools from anomaly_detection_client")                                           
                except Exception as e:
                    print(f"⚠️ Failed to get tools from MCP client: {e}")          

            # Create agent with all available tools            
            #TODO-9: Initialize the agent with all necessary tools and model created in earlier steps.

        else:
            print(f"♻️ Using existing agent instance with memory context")

    
        #TODO-10: code snippet to invoke the agent


        # print(f"✅ Agent response generated :: {response}")
        # Extract plain text response
        response_text = response.message['content'][0]['text']    
        # Return plain text (required by AgentCore Runtime)
        return response_text

    except Exception as error:
        print(f"❌ Error in agent invocation: {error}")
        # Return error message as plain text
        return f"I apologize, but I encountered a technical error: {str(error)}. Please try again."


if __name__ == "__main__":
    print("� Telecom Network Operations Agent")
    print("=" * 50)
    try:
        user_prompt = input("\n💬 Enter your query or incident description: ").strip()
        # Create payload with user input
        payload = {
            "prompt": user_prompt
        }
        
        print(f"\n🔄 Processing your request...")
        print("-" * 30)
        
        # Call the agent handler
        response = agent_handler(payload)

        print(f"\n📋 Agent Response :")
        print("-" * 30)
        print(response) 
        print("-" * 30)    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")