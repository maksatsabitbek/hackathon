import boto3
import json
import uuid

# Generate unique session ID
session_id = str(uuid.uuid4()) + "-" + str(uuid.uuid4())[:8]  # Ensures 33+ chars

agent_core_client = boto3.client('bedrock-agentcore', region_name='us-west-2')
#payload = json.dumps({"prompt": "which of the markets are active for the network operations. Get the details of all high priority active incidents. And help me with detailed steps to resolve those incidents. also mention the tools you used to find the responses. where possible mention the document references you used to get the steps to resolve the incidents"})
payload = json.dumps({"prompt": "which of the markets are active for the network operations. Get the details of all high priority active incidents."})

ssm = boto3.client('ssm', region_name='us-west-2')
agent_arn = ''
try:
    response = ssm.get_parameter(Name='AgentRuntimeArn')
    agent_arn = response['Parameter']['Value']
    print("agent arn :", agent_arn)
except Exception:
    print("Agent ARN not configured.")

print("session_id:", session_id)

response = agent_core_client.invoke_agent_runtime(
    agentRuntimeArn=agent_arn,
    runtimeSessionId=session_id,
    payload=payload,
    qualifier="DEFAULT"
)

response_body = response['response'].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)