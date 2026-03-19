"""Invoke the deployed K8s Expert Finder Agent on AgentCore Runtime."""

import boto3
import json
import uuid
import sys

REGION = "us-west-2"

session_id = str(uuid.uuid4())

agent_core_client = boto3.client("bedrock-agentcore", region_name=REGION)

ssm = boto3.client("ssm", region_name=REGION)
agent_arn = ""
try:
    response = ssm.get_parameter(Name="K8sExpertFinderAgentArn")
    agent_arn = response["Parameter"]["Value"]
    print("Agent ARN:", agent_arn)
except Exception:
    print("Agent ARN not configured in SSM. Deploy the agent first.")
    sys.exit(1)

if len(sys.argv) > 1:
    user_prompt = " ".join(sys.argv[1:])
else:
    user_prompt = (
        "I have a scheduling issue with pod priority and preemption in Kubernetes. "
        "Who are the top experts that can help me?"
    )

print(f"\nPrompt: {user_prompt}")
print(f"Session ID: {session_id}")
print("-" * 60)

payload = json.dumps({"prompt": user_prompt})

response = agent_core_client.invoke_agent_runtime(
    agentRuntimeArn=agent_arn,
    runtimeSessionId=session_id,
    payload=payload,
    qualifier="DEFAULT",
)

response_body = response["response"].read()
response_data = json.loads(response_body)
print("\nAgent Response:")
print("=" * 60)
print(response_data)
