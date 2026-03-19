"""Deploy K8s Expertise MCP Server to AgentCore Runtime."""

import os
import sys
import time
import json

from bedrock_agentcore_starter_toolkit import Runtime
import boto3

region = "us-west-2"
expertise_mcp_runtime_role = "k8s-expertise-mcp-runtime-role"
iam = boto3.client("iam", region_name=region)


def create_role_if_not_exists(role_name: str, trust_policy: dict, description: str) -> str:
    try:
        response = iam.get_role(RoleName=role_name)
        role_arn = response["Role"]["Arn"]
        print(f"Role already exists: {role_name}")
        return role_arn
    except iam.exceptions.NoSuchEntityException:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=description,
        )
        role_arn = response["Role"]["Arn"]
        print(f"Created IAM role: {role_name}")
        return role_arn


def attach_policy_if_not_attached(role_name: str, policy_arn: str):
    try:
        attached = iam.list_attached_role_policies(RoleName=role_name)
        if any(p["PolicyArn"] == policy_arn for p in attached["AttachedPolicies"]):
            print(f"  Policy already attached: {policy_arn.split('/')[-1]}")
        else:
            iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            print(f"  Attached policy: {policy_arn.split('/')[-1]}")
    except Exception as e:
        print(f"  Failed to attach policy: {e}")


def put_inline_policy_if_changed(role_name: str, policy_name: str, policy_document: dict):
    try:
        existing = iam.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        if existing["PolicyDocument"] == policy_document:
            print(f"  Inline policy unchanged: {policy_name}")
        else:
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
            )
            print(f"  Updated inline policy: {policy_name}")
    except iam.exceptions.NoSuchEntityException:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
        )
        print(f"  Created inline policy: {policy_name}")


def setup_mcp_runtime_role():
    print("Setting up MCP Server Runtime Role")
    role_name = expertise_mcp_runtime_role

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    role_arn = create_role_if_not_exists(
        role_name, trust_policy, "Execution role for K8s Expertise MCP Server"
    )

    attach_policy_if_not_attached(
        role_name, "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
    )
    attach_policy_if_not_attached(
        role_name, "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
    )

    mcp_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "SSMAccess",
                "Effect": "Allow",
                "Action": ["ssm:GetParameter", "ssm:GetParameters"],
                "Resource": f"arn:aws:ssm:{region}:*:parameter/*",
            },
            {
                "Sid": "BedrockInvoke",
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/*",
                    "arn:aws:bedrock:*::inference-profile/*",
                    f"arn:aws:bedrock:*:*:inference-profile/*",
                ],
            },
            {
                "Sid": "XRayTracing",
                "Effect": "Allow",
                "Action": ["xray:PutTraceSegments", "xray:PutTelemetryRecords"],
                "Resource": "*",
            },
        ],
    }
    put_inline_policy_if_changed(role_name, "MCPServerPermissions", mcp_policy)

    ecr_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                ],
                "Resource": "*",
            }
        ],
    }
    put_inline_policy_if_changed(role_name, "ECRAccess", ecr_policy)

    return role_arn


def deploy_mcp_server():
    print("Deploying K8s Expertise MCP Server to AgentCore Runtime")
    print(f"Using AWS region: {region}")

    execution_role_arn = expertise_mcp_runtime_role
    mcp_server_name = "k8s_expertise_mcp"

    print(f"Using execution role: {execution_role_arn}")

    agentcore_runtime = Runtime()

    print("Configuring AgentCore Runtime...")
    try:
        agentcore_runtime.configure(
            entrypoint="mcp_expertise_server.py",
            auto_create_execution_role=False,
            execution_role=execution_role_arn,
            auto_create_ecr=True,
            requirements_file="requirements.txt",
            region=region,
            protocol="MCP",
            agent_name=mcp_server_name,
        )
        print("Configuration completed")
    except Exception as e:
        print(f"Configuration failed: {e}")
        sys.exit(1)

    print("Launching MCP server (this takes 5-8 minutes)...")
    try:
        launch_result = agentcore_runtime.launch()
        print(f"Launch initiated")
        print(f"Agent ARN: {launch_result.agent_arn}")
        print(f"Agent ID: {launch_result.agent_id}")
    except Exception as e:
        print(f"Launch failed: {e}")
        sys.exit(1)

    print("Waiting for deployment to complete...")
    max_wait_time = 600
    start_time = time.time()

    while True:
        try:
            status_response = agentcore_runtime.status()
            status = status_response.endpoint["status"]
            if status == "READY":
                print("MCP Server is READY!")
                break
            elif status in ["CREATE_FAILED", "DELETE_FAILED", "UPDATE_FAILED"]:
                print(f"Deployment failed with status: {status}")
                sys.exit(1)
            else:
                print(f"   Status: {status}...")
        except Exception:
            print("   Checking status...")

        if time.time() - start_time > max_wait_time:
            print("Timeout waiting for deployment")
            sys.exit(1)

        time.sleep(10)

    print("Storing deployment information...")
    ssm_client = boto3.client("ssm", region_name=region)
    try:
        encoded_arn = launch_result.agent_arn.replace(":", "%3A").replace("/", "%2F")
        mcp_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations"

        ssm_client.put_parameter(
            Name="k8s_expertise_mcp_server_url",
            Value=mcp_url,
            Type="String",
            Description="K8s Expertise MCP Server URL",
            Overwrite=True,
        )
        print("Deployment info stored in SSM")
    except Exception as e:
        print(f"Warning: Could not store in Parameter Store: {e}")

    print("\n" + "=" * 60)
    print("MCP Server Deployment Successful!")
    print("=" * 60)
    print(f"MCP Server Name: {mcp_server_name}")
    print(f"Agent ARN: {launch_result.agent_arn}")
    print(f"MCP URL: {mcp_url}")
    print("\nAvailable Tools:")
    print("  - analyze_repository(repo_owner, repo_name)")
    print("  - list_domains()")
    print("  - get_domain_experts(domain_name)")
    print("  - get_contributor_profile(contributor_name)")

    return launch_result


if __name__ == "__main__":
    expertise_mcp_runtime_role = setup_mcp_runtime_role()
    print(f"Role ARN: {expertise_mcp_runtime_role}")
    deploy_mcp_server()
