"""Create DynamoDB table for Kubernetes expertise mapping.

Table: k8s-expertise-map
  PK: pk (String) - e.g. DOMAIN#scheduling, REPO#kubernetes/kubernetes
  SK: sk (String) - e.g. CONTRIBUTOR#user@email.com, METADATA
  GSI: sk-pk-index (SK -> PK) for querying all domains for a contributor
"""

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "k8s-expertise-map"
REGION = "us-west-2"

dynamodb_client = boto3.client("dynamodb", region_name=REGION)


def create_table_if_not_exists():
    try:
        dynamodb_client.describe_table(TableName=TABLE_NAME)
        print(f"Table {TABLE_NAME} already exists")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            print(f"Error checking table: {e}")
            return False

    print(f"Creating table {TABLE_NAME}...")
    try:
        dynamodb_client.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "sk-pk-index",
                    "KeySchema": [
                        {"AttributeName": "sk", "KeyType": "HASH"},
                        {"AttributeName": "pk", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
            Tags=[
                {"Key": "Project", "Value": "K8sExpertFinder"},
                {"Key": "Environment", "Value": "Hackathon"},
            ],
        )

        print("Waiting for table to be active...")
        waiter = dynamodb_client.get_waiter("table_exists")
        waiter.wait(TableName=TABLE_NAME)
        print(f"Table {TABLE_NAME} created successfully")
        return True

    except Exception as e:
        print(f"Failed to create table: {e}")
        return False


def main():
    print("=" * 60)
    print(f"DynamoDB Setup: {TABLE_NAME}")
    print(f"Region: {REGION}")
    print("=" * 60)

    if not create_table_if_not_exists():
        print("\nFailed to create/verify table")
        exit(1)

    print("\nSetup complete!")


if __name__ == "__main__":
    main()
