#!/bin/bash

# Check if AWS CLI is configured with valid credentials
check_aws_credentials() {
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "AWS credentials are not configured or are invalid. Please run 'aws configure' and try again."
        exit 1
    fi
}

# Function to check and install dependencies
check_dependencies() {
    # Check for AWS CLI
    if ! command -v aws &> /dev/null; then
        echo "AWS CLI is not installed. Installing..."
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip awscliv2.zip
        sudo ./aws/install
        rm -rf aws awscliv2.zip
    fi

    # Check for SAM CLI
    if ! command -v sam &> /dev/null; then
        echo "SAM CLI is not installed. Installing..."
        pip install aws-sam-cli
    fi

    # Check for Python
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 is not installed. Please install Python 3 and try again."
        exit 1
    fi

    # Check for zip
    if ! command -v zip &> /dev/null; then
        echo "zip is not installed. Installing..."
        sudo apt-get update && sudo apt-get install -y zip
    fi
}

deploy_frontend() {
    echo "Deploying frontend..."
    cd frontend
    ng cache clean
    npm install
    npm run build -- --configuration=production

    if [ $? -ne 0 ]; then
        echo "Build failed. Exiting."
        exit 1
    fi

    # Check for .env file and source it if it exists
    if [ -f .env ]; then
        echo "Found .env file. Loading environment variables..."
        export $(grep -v '^#' .env | xargs)
    fi

    if [ -z "$S3_BUCKET" ]; then
        echo "Error: S3_BUCKET is not set in .env file"
        exit 1
    fi
    
    if [ -n "$S3_BUCKET" ]; then
        # Clear existing contents of the S3 bucket
        echo "Clearing existing contents of S3 bucket..."
        aws s3 rm s3://$S3_BUCKET --recursive

        # Configure bucket for static website hosting
        echo "Configuring bucket for static website hosting..."
        aws s3 website s3://$S3_BUCKET --index-document index.html --error-document index.html

        # Set bucket policy for public read access
        echo "Setting bucket policy for public read access..."
        aws s3api put-bucket-policy --bucket $S3_BUCKET --policy "{
            \"Version\": \"2012-10-17\",
            \"Statement\": [
                {
                    \"Sid\": \"PublicReadGetObject\",
                    \"Effect\": \"Allow\",
                    \"Principal\": \"*\",
                    \"Action\": \"s3:GetObject\",
                    \"Resource\": \"arn:aws:s3:::$S3_BUCKET/*\"
                }
            ]
        }"

        # Sync built files to S3
        echo "Syncing files to S3..."
        aws s3 sync dist/frontend/browser s3://$S3_BUCKET --delete
        
        if [ $? -eq 0 ]; then
            echo "Sync completed successfully."
        else
            echo "Error: Sync to S3 failed."
            exit 1
        fi

        # List contents of the bucket to verify update
        echo "Listing contents of S3 bucket:"
        aws s3 ls s3://$S3_BUCKET --recursive --human-readable --summarize

        # Output the website URL
        echo "Frontend deployed to: http://$S3_BUCKET.s3-website-us-east-1.amazonaws.com"
        echo "Please clear your browser cache or use incognito mode to see the latest changes."
        
        cd ..
    fi
}

deploy_stt() {
    echo "Deploying STT Process..."
    cd stt-process

    # Check for .env file and source it if it exists
    if [ -f .env ]; then
        echo "Found .env file. Loading environment variables..."
        export $(grep -v '^#' .env | xargs)
    fi

    # Initiate build
    sam build
    
    if [ $? -ne 0 ]; then
        echo "Error: SAM build failed"
        exit 1
    fi
    
    # Fetch the StateMachineArn
    STT_WORKFLOW_ARN=$(aws cloudformation describe-stacks --stack-name ja-stt-statemachine --query "Stacks[0].Outputs[?OutputKey=='TranscriptionWorkflowArn'].OutputValue" --output text)
    
    # Deploy with or without OPENAI_API_KEY
    if [ -n "$OPENAI_API_KEY" ]; then
        echo "Using OPENAI_API_KEY from .env file"
        sam deploy --stack-name ja-stt --capabilities CAPABILITY_IAM --region us-east-1 --no-confirm-changeset \
            --parameter-overrides \
            ParameterKey=OpenAIApiKey,ParameterValue=$OPENAI_API_KEY \
            ParameterKey=StateMachineArn,ParameterValue=$STT_WORKFLOW_ARN
    else
        echo "OPENAI_API_KEY not found in .env file. Deployment may fail."
        sam deploy --stack-name ja-stt --capabilities CAPABILITY_IAM --region us-east-1 --no-confirm-changeset \
            --parameter-overrides \
            ParameterKey=StateMachineArn,ParameterValue=$STT_WORKFLOW_ARN
    fi
    
    if [ $? -ne 0 ]; then
        echo "Error: SAM deploy failed"
        exit 1
    fi
    
    # Cleanup the Python layer zip file after deployment
    cleanup_python_layer

    cd ..
    
    AUDIO_UPLOADS_BUCKET=$(aws cloudformation describe-stacks --stack-name ja-stt --query "Stacks[0].Outputs[?OutputKey=='AudioUploadsBucketName'].OutputValue" --output text)
    TRANSCRIPTION_OUTPUT_BUCKET=$(aws cloudformation describe-stacks --stack-name ja-stt --query "Stacks[0].Outputs[?OutputKey=='TranscriptionOutputBucketName'].OutputValue" --output text)
    STT_PROCESS_URL=$(aws cloudformation describe-stacks --stack-name ja-stt --query "Stacks[0].Outputs[?OutputKey=='STTProcessUrl'].OutputValue" --output text)
    
    echo "STT Process URL: $STT_PROCESS_URL"
    echo "Audio Uploads Bucket: $AUDIO_UPLOADS_BUCKET"
    echo "Transcription Output Bucket: $TRANSCRIPTION_OUTPUT_BUCKET"
    echo "STT Process deployment completed successfully"
}

deploy_statemachine() {
    echo "Deploying State Machine..."
    cd stt-process/statemachine

    # Initiate build
    sam build
    
    if [ $? -ne 0 ]; then
        echo "Error: SAM build failed"
        exit 1
    fi
    
    # Deploy the state machine
    sam deploy --stack-name ja-stt-statemachine --capabilities CAPABILITY_IAM --region us-east-1 --no-confirm-changeset \
        --parameter-overrides \
        ParameterKey=DataLambdaArn,ParameterValue=$(aws cloudformation describe-stacks --stack-name ja-stt --query "Stacks[0].Outputs[?OutputKey=='DataLambdaArn'].OutputValue" --output text) \
        ParameterKey=TranscribeLambdaArn,ParameterValue=$(aws cloudformation describe-stacks --stack-name ja-stt --query "Stacks[0].Outputs[?OutputKey=='TranscribeLambdaArn'].OutputValue" --output text) \
        ParameterKey=EnhanceLambdaArn,ParameterValue=$(aws cloudformation describe-stacks --stack-name ja-stt --query "Stacks[0].Outputs[?OutputKey=='EnhanceLambdaArn'].OutputValue" --output text) \
        ParameterKey=StoreLambdaArn,ParameterValue=$(aws cloudformation describe-stacks --stack-name ja-stt --query "Stacks[0].Outputs[?OutputKey=='StoreLambdaArn'].OutputValue" --output text)
    
    if [ $? -ne 0 ]; then
        echo "Error: SAM deploy failed"
        exit 1
    fi

    cd ../..
}

cleanup_python_layer() {
    echo "Cleaning up Python layer zip file..."
    rm -f python.zip
}

# Fail-safe
set -eo pipefail

# Check and install dependencies
check_dependencies
check_aws_credentials

# Deploy based on the provided argument
if [ "$1" == "frontend" ]; then
    deploy_frontend
elif [ "$1" == "stt-process" ]; then
    deploy_stt
elif [ "$1" == "statemachine" ]; then
    deploy_statemachine
elif [ "$1" == "all" ]; then
    deploy_frontend
    deploy_statemachine
    deploy_stt
else
    echo "Invalid command. Please use one of the following arguments:"
    echo "  frontend     - Deploy the frontend"
    echo "  stt-process  - Deploy the STT process"
    echo "  statemachine - Deploy the state machine"
    echo "  all          - Deploy everything"
fi