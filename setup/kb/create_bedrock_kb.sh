#!/bin/bash

# Create S3 bucket, upload kb-data, and create Bedrock Knowledge Base

REGION="us-west-2"
BUCKET_PREFIX="telco-agenticai-ws"
KB_NAME="telco-service-assurance-kb"
KB_DESCRIPTION="Knowledge base for telecom network issue resolution"
EMBEDDING_MODEL="amazon.titan-embed-text-v2:0"
KB_DATA_DIR="kb-data"

echo "============================================================"
echo "Bedrock Knowledge Base Setup"
echo "Region: $REGION"
echo "============================================================"

# Get AWS account ID
echo "Getting AWS account ID..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [ -z "$ACCOUNT_ID" ]; then
    echo "❌ Error: Could not retrieve account ID"
    exit 1
fi

echo "Account ID: $ACCOUNT_ID"

# Get current date
DATE_SUFFIX=$(date +%Y%m%d)
echo "Date: $DATE_SUFFIX"

# Define bucket name
DATA_BUCKET="${BUCKET_PREFIX}-${ACCOUNT_ID}-${DATE_SUFFIX}"
echo "Data bucket: $DATA_BUCKET"

# Step 1: Create S3 bucket
echo ""
echo "============================================================"
echo "Step 1: Creating S3 Bucket"
echo "============================================================"

# Check if bucket already exists
if aws s3 ls "s3://${DATA_BUCKET}" 2>/dev/null; then
    echo "✅ Bucket $DATA_BUCKET already exists"
else
    # Create the bucket
    echo "Creating bucket $DATA_BUCKET..."
    
    if [ "$REGION" == "us-east-1" ]; then
        aws s3api create-bucket --bucket "$DATA_BUCKET" --region "$REGION"
    else
        aws s3api create-bucket \
            --bucket "$DATA_BUCKET" \
            --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION"
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ Bucket created successfully"
        
        # Enable default encryption
        aws s3api put-bucket-encryption \
            --bucket "$DATA_BUCKET" \
            --server-side-encryption-configuration '{
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    },
                    "BucketKeyEnabled": true
                }]
            }' \
            --region "$REGION"
        
        # Block public access
        aws s3api put-public-access-block \
            --bucket "$DATA_BUCKET" \
            --public-access-block-configuration \
                "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
            --region "$REGION"
        
        echo "✅ Bucket security configured"
    else
        echo "❌ Failed to create bucket"
        exit 1
    fi
fi

# Step 2: Upload kb-data files to S3
echo ""
echo "============================================================"
echo "Step 2: Uploading kb-data files to S3"
echo "============================================================"

if [ ! -d "$KB_DATA_DIR" ]; then
    echo "❌ Error: kb-data directory not found at $KB_DATA_DIR"
    exit 1
fi

aws s3 cp "$KB_DATA_DIR" "s3://$DATA_BUCKET/kb-data/" --recursive --region "$REGION"

if [ $? -eq 0 ]; then
    echo "✅ Files copied successfully"
    echo ""
    echo "Files in bucket:"
    aws s3 ls "s3://$DATA_BUCKET/kb-data/" --region "$REGION"
else
    echo "❌ Failed to copy files"
    exit 1
fi

# Step 3: Create IAM role for Knowledge Base
echo ""
echo "============================================================"
echo "Step 3: Creating IAM role for Knowledge Base"
echo "============================================================"
ROLE_NAME="BedrockKnowledgeBaseRole-${DATE_SUFFIX}"

# Create trust policy
cat > /tmp/kb-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document file:///tmp/kb-trust-policy.json \
    --description "Role for Bedrock Knowledge Base" 2>/dev/null

# Create comprehensive policy with all required permissions
POLICY_NAME="BedrockKnowledgeBasePolicy-${DATE_SUFFIX}"
cat > /tmp/kb-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3DataSourceAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${DATA_BUCKET}",
        "arn:aws:s3:::${DATA_BUCKET}/*"
      ]
    },
    {
      "Sid": "S3VectorBucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3vectors:PutVectors",
        "s3vectors:GetVectors",
        "s3vectors:DeleteVectors",
        "s3vectors:QueryVectors",
        "s3vectors:GetIndex"
      ],
      "Resource": "arn:aws:s3vectors:${REGION}:${ACCOUNT_ID}:bucket/${BUCKET_PREFIX}-vectors-${ACCOUNT_ID}-${DATE_SUFFIX}/index/bedrock-knowledge-base-index"
    },
    {
      "Sid": "BedrockModelAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:${REGION}::foundation-model/${EMBEDDING_MODEL}"
    }
  ]
}
EOF

POLICY_ARN=$(aws iam create-policy \
    --policy-name "$POLICY_NAME" \
    --policy-document file:///tmp/kb-policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null)

if [ -z "$POLICY_ARN" ]; then
    # Policy might already exist, try to get it
    POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"
fi

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN"

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo "✅ IAM role created: $ROLE_ARN"

# Wait for role to propagate
echo "Waiting for IAM role to propagate..."
sleep 10

# Step 4: Create Knowledge Base (using S3 as vector store)
echo ""
echo "============================================================"
echo "Step 4: Creating Knowledge Base with S3 Vector Store"
echo "============================================================"

# Create S3 Vector bucket (with vector capabilities)
VECTOR_BUCKET="${BUCKET_PREFIX}-vectors-${ACCOUNT_ID}-${DATE_SUFFIX}"
echo "Creating S3 Vector bucket: $VECTOR_BUCKET"

# Check if S3 Vector bucket already exists
if aws s3vectors get-vector-bucket --vector-bucket-name "$VECTOR_BUCKET" --region "$REGION" >/dev/null 2>&1; then
    echo "✅ S3 Vector bucket $VECTOR_BUCKET already exists"
else
    # Create S3 Vector bucket using s3vectors API
    aws s3vectors create-vector-bucket \
        --vector-bucket-name "$VECTOR_BUCKET" \
        --region "$REGION"

    if [ $? -eq 0 ]; then
        echo "✅ S3 Vector bucket created: $VECTOR_BUCKET"
    else
        echo "❌ Failed to create S3 Vector bucket"
        exit 1
    fi
fi

# Configure bucket security for vector bucket
echo "Configuring S3 Vector bucket security..."
aws s3api put-bucket-encryption \
    --bucket "$VECTOR_BUCKET" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            },
            "BucketKeyEnabled": true
        }]
    }' \
    --region "$REGION" 2>/dev/null

aws s3api put-public-access-block \
    --bucket "$VECTOR_BUCKET" \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
    --region "$REGION" 2>/dev/null

echo "✅ S3 Vector bucket security configured"
    
# Create vector index in the bucket
VECTOR_INDEX_NAME="bedrock-knowledge-base-index"
echo "Creating vector index: $VECTOR_INDEX_NAME"

# Check if vector index already exists
if aws s3vectors get-index --vector-bucket-name "$VECTOR_BUCKET" --index-name "$VECTOR_INDEX_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "✅ Vector index $VECTOR_INDEX_NAME already exists"
else
    # Configure Bedrock metadata fields as non-filterable to avoid 2KB limit
    cat > /tmp/metadata-config.json <<EOF
{
  "nonFilterableMetadataKeys": [
    "AMAZON_BEDROCK_TEXT_CHUNK",
    "AMAZON_BEDROCK_METADATA",
    "AMAZON_BEDROCK_SOURCE_URI",
    "AMAZON_BEDROCK_DOCUMENT_ID",
    "x-amz-bedrock-kb-source-uri",
    "x-amz-bedrock-kb-chunk-id",
    "x-amz-bedrock-kb-data-source-id",
    "x-amz-bedrock-kb-knowledge-base-id"
  ]
}
EOF

    aws s3vectors create-index \
        --vector-bucket-name "$VECTOR_BUCKET" \
        --index-name "$VECTOR_INDEX_NAME" \
        --data-type "float32" \
        --dimension 1024 \
        --distance-metric "cosine" \
        --metadata-configuration file:///tmp/metadata-config.json \
        --region "$REGION"
    
    if [ $? -eq 0 ]; then
        echo "✅ Vector index created: $VECTOR_INDEX_NAME"
    else
        echo "❌ Failed to create vector index"
        exit 1
    fi
fi



# Create Knowledge Base configuration JSON
cat > /tmp/kb-config.json <<EOF
{
  "name": "${KB_NAME}",
  "description": "${KB_DESCRIPTION}",
  "roleArn": "${ROLE_ARN}",
  "knowledgeBaseConfiguration": {
    "type": "VECTOR",
    "vectorKnowledgeBaseConfiguration": {
      "embeddingModelArn": "arn:aws:bedrock:${REGION}::foundation-model/${EMBEDDING_MODEL}"
    }
  },
  "storageConfiguration": {
    "type": "S3_VECTORS",
    "s3VectorsConfiguration": {
      "vectorBucketArn": "arn:aws:s3vectors:${REGION}:${ACCOUNT_ID}:bucket/${VECTOR_BUCKET}",
      "indexName": "${VECTOR_INDEX_NAME}"
    }
  }
}
EOF

KB_ID=$(aws bedrock-agent create-knowledge-base \
    --cli-input-json file:///tmp/kb-config.json \
    --region "$REGION" \
    --query 'knowledgeBase.knowledgeBaseId' \
    --output text 2>&1)

if [[ "$KB_ID" == *"error"* ]] || [ -z "$KB_ID" ]; then
    echo "❌ Failed to create Knowledge Base"
    echo "$KB_ID"
    exit 1
fi

echo "✅ Knowledge Base created: $KB_ID"

# Wait for Knowledge Base to be active
echo "Waiting for Knowledge Base to become active..."
MAX_WAIT=300  # 5 minutes
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    KB_STATUS=$(aws bedrock-agent get-knowledge-base \
        --knowledge-base-id "$KB_ID" \
        --region "$REGION" \
        --query 'knowledgeBase.status' \
        --output text 2>/dev/null)
    
    if [ "$KB_STATUS" == "ACTIVE" ]; then
        echo "✅ Knowledge Base is active"
        break
    elif [ "$KB_STATUS" == "FAILED" ]; then
        echo "❌ Knowledge Base creation failed"
        exit 1
    fi
    
    echo "  Status: $KB_STATUS (waiting...)"
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "❌ Timeout waiting for Knowledge Base to become active"
    exit 1
fi

# Step 5: Create Data Source
echo ""
echo "============================================================"
echo "Step 5: Creating Data Source"
echo "============================================================"

DS_ID=$(aws bedrock-agent create-data-source \
    --knowledge-base-id "$KB_ID" \
    --name "telco-kb-data-source" \
    --description "S3 data source for telecom knowledge base" \
    --data-source-configuration "type=S3,s3Configuration={bucketArn=arn:aws:s3:::${DATA_BUCKET},inclusionPrefixes=[kb-data/]}" \
    --region "$REGION" \
    --query 'dataSource.dataSourceId' \
    --output text)

if [ $? -eq 0 ] && [ -n "$DS_ID" ]; then
    echo "✅ Data Source created: $DS_ID"
else
    echo "❌ Failed to create Data Source"
    exit 1
fi

# Wait for Data Source to be available
echo "Waiting for Data Source to be available..."
MAX_WAIT_DS=60  # 1 minute
ELAPSED_DS=0
while [ $ELAPSED_DS -lt $MAX_WAIT_DS ]; do
    DS_STATUS=$(aws bedrock-agent get-data-source \
        --knowledge-base-id "$KB_ID" \
        --data-source-id "$DS_ID" \
        --region "$REGION" \
        --query 'dataSource.status' \
        --output text 2>/dev/null)
    
    if [ "$DS_STATUS" == "AVAILABLE" ]; then
        echo "✅ Data Source is available"
        break
    elif [ "$DS_STATUS" == "FAILED" ]; then
        echo "❌ Data Source creation failed"
        exit 1
    fi
    
    echo "  Status: $DS_STATUS (waiting...)"
    sleep 5
    ELAPSED_DS=$((ELAPSED_DS + 5))
done

if [ $ELAPSED_DS -ge $MAX_WAIT_DS ]; then
    echo "❌ Timeout waiting for Data Source to become available"
    exit 1
fi

# Step 6: Start ingestion job
echo ""
echo "============================================================"
echo "Step 6: Starting ingestion job"
echo "============================================================"

INGESTION_JOB_ID=$(aws bedrock-agent start-ingestion-job \
    --knowledge-base-id "$KB_ID" \
    --data-source-id "$DS_ID" \
    --region "$REGION" \
    --query 'ingestionJob.ingestionJobId' \
    --output text)

if [ $? -eq 0 ] && [ -n "$INGESTION_JOB_ID" ]; then
    echo "✅ Ingestion job started: $INGESTION_JOB_ID"
else
    echo "❌ Failed to start ingestion job"
    exit 1
fi

# Step 7: Store Knowledge Base ID in SSM Parameter Store
echo ""
echo "============================================================"
echo "Step 7: Storing Knowledge Base ID in SSM Parameter Store"
echo "============================================================"

PARAMETER_NAME="telco_anomaly_resolution_runbooks_kb"
aws ssm put-parameter \
    --name "$PARAMETER_NAME" \
    --value "$KB_ID" \
    --type "String" \
    --description "Knowledge Base ID for Telecom Anomaly Resolution Runbooks" \
    --overwrite \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo "✅ Knowledge Base ID stored in SSM Parameter: $PARAMETER_NAME"
else
    echo "❌ Failed to store Knowledge Base ID in SSM Parameter Store"
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ Setup complete!"
echo "============================================================"
echo "Knowledge Base ID: $KB_ID"
echo "Data Source ID: $DS_ID"
echo "Ingestion Job ID: $INGESTION_JOB_ID"
echo "SSM Parameter: $PARAMETER_NAME = $KB_ID"
echo "Region: $REGION"
echo ""
echo "Monitor ingestion status with:"
echo "aws bedrock-agent get-ingestion-job \\"
echo "  --knowledge-base-id $KB_ID \\"
echo "  --data-source-id $DS_ID \\"
echo "  --ingestion-job-id $INGESTION_JOB_ID \\"
echo "  --region $REGION"
echo ""
echo "Retrieve Knowledge Base ID from SSM with:"
echo "aws ssm get-parameter --name $PARAMETER_NAME --region $REGION --query 'Parameter.Value' --output text"

# Clean up temp files
rm -f /tmp/kb-trust-policy.json /tmp/kb-policy.json /tmp/kb-config.json /tmp/metadata-config.json
