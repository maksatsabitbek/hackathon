"""Deploy K8s Expert Finder Agent to AgentCore Runtime."""

import os
import sys
import time
import json

from bedrock_agentcore_starter_toolkit import Runtime
import boto3

region = "us-west-2"
expert_agent_runtime_role = "k8s-expert-finder-agent-runtime-role"
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


def setup_agent_runtime_role():
    print("Setting up Agent Runtime Role")
    role_name = expert_agent_runtime_role

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
        role_name, trust_policy, "Execution role for K8s Expert Finder Agent"
    )

    attach_policy_if_not_attached(
        role_name, "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
    )

    agent_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "InvokeMCPServer",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:InvokeAgentRuntime",
                    "bedrock-agentcore:GetAgentRuntime",
                ],
                "Resource": f"arn:aws:bedrock-agentcore:{region}:*:runtime/*",
            },
            {
                "Sid": "ReadSSMParameters",
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParametersByPath",
                ],
                "Resource": f"arn:aws:ssm:{region}:*:parameter/*",
            },
            {
                "Sid": "InvokeBedrockModels",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/*",
                    "arn:aws:bedrock:*::inference-profile/*",
                    f"arn:aws:bedrock:*:*:inference-profile/*",
                ],
            },
            {
                "Sid": "XRayTracing",
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                ],
                "Resource": "*",
            },
        ],
    }
    put_inline_policy_if_changed(role_name, "AgentPermissions", agent_policy)

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


def deploy_agent():
    print("Deploying K8s Expert Finder Agent to AgentCore Runtime")
    print(f"Using AWS region: {region}")

    execution_role_arn = expert_agent_runtime_role
    agent_name = "k8s_expert_finder_agent"

    print(f"Using execution role: {execution_role_arn}")

    agentcore_runtime = Runtime()

    print("Configuring AgentCore Runtime...")
    try:
        agentcore_runtime.configure(
            entrypoint="expert_finder_agent.py",
            auto_create_execution_role=False,
            execution_role=execution_role_arn,
            auto_create_ecr=True,
            requirements_file="requirements.txt",
            region=region,
            agent_name=agent_name,
        )
        print("Configuration completed")
    except Exception as e:
        print(f"Configuration failed: {e}")
        sys.exit(1)

    print("Launching Agent (this takes 5-8 minutes)...")
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
                print("Agent is READY!")
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
        ssm_client.put_parameter(
            Name="K8sExpertFinderAgentArn",
            Value=launch_result.agent_arn,
            Type="String",
            Description="K8s Expert Finder Agent ARN",
            Overwrite=True,
        )
        print("Agent ARN stored in SSM Parameter Store")
    except Exception as e:
        print(f"Warning: Could not store in Parameter Store: {e}")

    print("\n" + "=" * 60)
    print("Agent Deployment Successful!")
    print("=" * 60)
    print(f"Agent Name: {agent_name}")
    print(f"Agent ARN: {launch_result.agent_arn}")

    return launch_result


if __name__ == "__main__":
    expert_agent_runtime_role = setup_agent_runtime_role()
    print(f"Role ARN: {expert_agent_runtime_role}")
    deploy_agent()
