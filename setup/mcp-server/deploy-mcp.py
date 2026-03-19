"""Deploy Anomaly Detection MCP Server to AgentCore Runtime."""

import os
import sys
import time
import json

from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
import boto3


region = "us-west-2"
anomaly_mcp_runtime_role = "telco-anomalies-mcp-runtime-role"
# Initialize IAM client
iam = boto3.client('iam', region_name=region)


def create_role_if_not_exists(role_name: str, trust_policy: dict, description: str) -> str:
    """Create IAM role if it doesn't exist, return ARN"""
    try:
        # Check if role exists
        response = iam.get_role(RoleName=role_name)
        role_arn = response['Role']['Arn']
        print(f"✅ Role already exists: {role_name}")
        return role_arn
    except iam.exceptions.NoSuchEntityException:
        # Create role
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=description
        )
        role_arn = response['Role']['Arn']
        print(f"✅ Created IAM role: {role_name}")
        return role_arn

def attach_policy_if_not_attached(role_name: str, policy_arn: str):
    """Attach managed policy to role if not already attached"""
    try:
        attached_policies = iam.list_attached_role_policies(RoleName=role_name)
        if any(p['PolicyArn'] == policy_arn for p in attached_policies['AttachedPolicies']):
            print(f"  ↳ Policy already attached: {policy_arn.split('/')[-1]}")
        else:
            iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            print(f"  ↳ Attached policy: {policy_arn.split('/')[-1]}")
    except Exception as e:
        print(f"  ⚠️  Failed to attach policy: {e}")


def put_inline_policy_if_changed(role_name: str, policy_name: str, policy_document: dict):
    """Put inline policy if it doesn't exist or has changed"""
    try:
        # Check if policy exists
        existing_policy = iam.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        if existing_policy['PolicyDocument'] == policy_document:
            print(f"  ↳ Inline policy unchanged: {policy_name}")
        else:
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            print(f"  ↳ Updated inline policy: {policy_name}")
    except iam.exceptions.NoSuchEntityException:
        # Create policy
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        print(f"  ↳ Created inline policy: {policy_name}")


def setup_mcp_runtime_role():
    """Create IAM role for MCP Server Runtime"""
    print("Setting up MCP Server Runtime Role")
    role_name = anomaly_mcp_runtime_role

    # Trust policy (Bedrock AgentCore can assume this role)
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    # Create role
    role_arn = create_role_if_not_exists(
        role_name,
        trust_policy,
        "Execution role for MCP Server Runtime (Anomaly Detection)"
    )

    # Attach basic execution policy for CloudWatch Logs
    attach_policy_if_not_attached(
        role_name,
        'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess'
    )

    # Attach readonly access policy for Dynamodb
    attach_policy_if_not_attached(
        role_name,
        'arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess'
    )

    # Inline policy for ECR access (required by AgentCore Runtime to pull Docker images)
    ecr_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchGetImage",
                "ecr:GetDownloadUrlForLayer"
            ],
            "Resource": "*"
        }]
    }

    put_inline_policy_if_changed(role_name, "ECRAccess", ecr_policy)

    return role_arn


def deploy_mcp_server():
    """Deploy the MCP server to AgentCore Runtime."""

    print("Deploying Anomaly Detection MCP Server to AgentCore Runtime")
    print(f"Using AWS region: {region}")

    # Get AWS account ID and construct IAM role ARN
    sts_client = boto3.client('sts', region_name=region)
    account_id = sts_client.get_caller_identity()['Account']
    execution_role_arn = anomaly_mcp_runtime_role
    mcp_server_name = "telco_anomaly_mcp"

    print(f"Using execution role: {execution_role_arn}")

    # Initialize AgentCore Runtime
    agentcore_runtime = Runtime()

    # Configure the runtime
    print("Configuring AgentCore Runtime...")
    print("Note: MCP server will be publicly accessible (for Runtime-to-Runtime calls)")

    try:
        # Use pre-created IAM role with all necessary permissions
        # Configure AgentCore Runtime with entrypoint agent, protocol, execution role, name
        response = agentcore_runtime.configure(
            entrypoint="mcp_anomaly_server.py",
            auto_create_execution_role=False,
            execution_role=execution_role_arn,
            auto_create_ecr=True,
            requirements_file="requirements.txt",
            region=region,
            protocol="MCP",
            agent_name=mcp_server_name
        )
        print("Configuration completed")
    except Exception as e:
        print(f"Configuration failed: {e}")
        sys.exit(1)

    # Launch the runtime
    print("Launching MCP server (this takes 5-8 minutes)...")

    try:
        launch_result = agentcore_runtime.launch()
        print(f"Launch initiated")
        print(f"MCP/Agent ARN: {launch_result.agent_arn}")
        print(f"MCP/Agent ID: {launch_result.agent_id}")
    except Exception as e:
        print(f"Launch failed: {e}")
        sys.exit(1)

    # Wait for deployment to complete
    print("Waiting for deployment to complete...")

    max_wait_time = 600  # 10 minutes
    start_time = time.time()

    while True:
        try:
            status_response = agentcore_runtime.status()
            status = status_response.endpoint['status']

            if status == 'READY':
                print("MCP Server is READY!")
                break
            elif status in ['CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED']:
                print(f"Deployment failed with status: {status}")
                sys.exit(1)
            else:
                print(f"   Status: {status}...")

        except Exception as e:
            print(f"   Checking status...")

        if time.time() - start_time > max_wait_time:
            print("Timeout waiting for deployment")
            sys.exit(1)

        time.sleep(10)

    # Store deployment info for agent to use
    print("Storing deployment information...")

    # Store in Parameter Store for easy retrieval
    ssm_client = boto3.client('ssm', region_name=region)

    try:
        ssm_client.put_parameter(
            Name='telco_anomaly_detection_mcp_server_url',
            Value=launch_result.agent_arn,
            Type='String',
            Description='Telco Anomaly Detection MCP Server ARN',
            Overwrite=True
        )

        # Construct MCP URL
        encoded_arn = launch_result.agent_arn.replace(':', '%3A').replace('/', '%2F')
        mcp_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations"

        ssm_client.put_parameter(
            Name='telco_anomaly_detection_mcp_server_url',
            Value=mcp_url,
            Type='String',
            Description='Telco Anomaly Detection MCP Server URL',
            Overwrite=True
        )

        print("✅ Deployment info stored")
    except Exception as e:
        print(f"Warning: Could not store in Parameter Store: {e}")

    # Print summary
    print("\n" + "="*60)
    print("MCP Server Deployment Successful!!")
    print("="*60)
    print(f"MCP Server Name: {mcp_server_name}")
    print ("launch_result :: ", launch_result)
    print(f"Agent ARN: {launch_result.agent_arn}")
    print (f"anomaly_mcp_runtime_role arn :: {anomaly_mcp_runtime_role}")
    print(f"MCP URL: {mcp_url}")
    print("\n[bold]Available Tools:[/bold]")
    print("  - detect_anomaly(market: str)")
    print("  - get_anomaly_details(anomaly_id: str)")
    print("  - list_active_markets()")

    return launch_result


if __name__ == "__main__":
    anomaly_mcp_runtime_role = setup_mcp_runtime_role()
    print ("anomaly_mcp_runtime_role :: ", anomaly_mcp_runtime_role)
    deploy_mcp_server()