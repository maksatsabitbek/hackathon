"""Load anomaly data into DynamoDB table.
This script loads data from anomalies.json into the telco-anomalies-synthetics table.
"""

import json
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "telco-anomalies-synthetic-data"
REGION = "us-west-2"

dynamodb_client = boto3.client("dynamodb", region_name=REGION)
dynamodb_resource = boto3.resource("dynamodb", region_name=REGION)


def create_table_if_not_exists():
    """Create the DynamoDB table if it doesn't exist."""
    try:
        # Check if table exists
        dynamodb_client.describe_table(TableName=TABLE_NAME)
        print(f"✅ Table {TABLE_NAME} already exists")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            print(f"❌ Error checking table: {e}")
            return False

    # Table doesn't exist, create it
    print(f"Creating table {TABLE_NAME}...")
    try:
        dynamodb_client.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "anomaly_id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "anomaly_id", "AttributeType": "S"},
                {"AttributeName": "market", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "market-index",
                    "KeySchema": [
                        {"AttributeName": "market", "KeyType": "HASH"},
                        {"AttributeName": "timestamp", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
            Tags=[
                {"Key": "Workshop", "Value": "TelcoAgenticAI"},
                {"Key": "Environment", "Value": "Development"},
            ],
        )

        # Wait for table to be active
        print("Waiting for table to be active...")
        waiter = dynamodb_client.get_waiter("table_exists")
        waiter.wait(TableName=TABLE_NAME)
        print(f"✅ Table {TABLE_NAME} created successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to create table: {e}")
        return False


def load_anomalies_from_json():
    """Load anomaly data from JSON file into DynamoDB table."""
    # Get the JSON file path
    json_file = Path(__file__).parent / "telco-anomalies.json"
    
    if not json_file.exists():
        print(f"❌ Error: {json_file} not found")
        return False
    
    # Load data from JSON
    print(f"Loading data from {json_file}...")
    with open(json_file, "r") as f:
        anomalies = json.load(f)
    
    print(f"Found {len(anomalies)} anomalies to load")
    
    # Get DynamoDB table
    table = dynamodb_resource.Table(TABLE_NAME)
    
    # Load data using batch writer for efficiency
    print(f"Loading data into {TABLE_NAME}...")
    try:
        with table.batch_writer() as batch:
            for i, anomaly in enumerate(anomalies, 1):
                batch.put_item(Item=anomaly)
                print(f"  Loaded {i}/{len(anomalies)}: {anomaly['anomaly_id']}")
        
        print(f"✅ Successfully loaded {len(anomalies)} anomalies into {TABLE_NAME}")
        return True
        
    except ClientError as e:
        print(f"❌ Error loading data: {e}")
        return False


def main():
    """Main function to create table and load anomaly data."""
    print("=" * 60)
    print(f"DynamoDB Setup: {TABLE_NAME}")
    print(f"Region: {REGION}")
    print("=" * 60)
    
    # Step 1: Create table if it doesn't exist
    if not create_table_if_not_exists():
        print("\n❌ Failed to create/verify table")
        exit(1)
    
    print()
    
    # Step 2: Load data
    success = load_anomalies_from_json()
    
    if success:
        print("\n✅ Setup complete!")
    else:
        print("\n❌ Data load failed")
        exit(1)


if __name__ == "__main__":
    main()