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

deploy_microservices() {
    echo "Deploying microservices..."
    cd microservices

    # Check for .env file and source it if it exists
    if [ -f .env ]; then
        echo "Found .env file. Loading environment variables..."
        export $(grep -v '^#' .env | xargs)
    fi

    sam build
    if [ $? -ne 0 ]; then
        echo "Error: SAM build failed"
        exit 1
    fi
    
    # Check if OPENAI_API_KEY is set and add it to parameter overrides if it exists
    if [ -n "$OPENAI_API_KEY" ]; then
        echo "Using OPENAI_API_KEY from .env file"
        sam deploy --stack-name metis-microservices --capabilities CAPABILITY_IAM --region us-east-1 --no-confirm-changeset --parameter-overrides OpenAIApiKey=$OPENAI_API_KEY
    else
        echo "OPENAI_API_KEY not found in .env file. Deployment may fail."
        sam deploy --stack-name metis-microservices --capabilities CAPABILITY_IAM --region us-east-1 --no-confirm-changeset
    fi

    if [ $? -ne 0 ]; then
        echo "Error: SAM deploy failed"
        exit 1
    fi

    cd ..
    MICROSERVICE_URL=$(aws cloudformation describe-stacks --stack-name metis-microservices --query "Stacks[0].Outputs[?OutputKey=='LLMFunctionUrl'].OutputValue" --output text)
    echo "Microservices LLM Function URL: $MICROSERVICE_URL"
    echo "Microservices deployment completed successfully"
}

# Check and install dependencies
check_dependencies
check_aws_credentials

# Check command line argument
if [ "$1" = "frontend" ]; then
    deploy_frontend
elif [ "$1" = "microservices" ]; then
    deploy_microservices
elif [ "$1" = "all" ]; then
    deploy_microservices
    deploy_frontend
else
    echo "Usage: ./deploy.sh [frontend|microservices|all]"
    exit 1
fi