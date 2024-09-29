import boto3
import json
import os

sfn_client = boto3.client('stepfunctions')

def lambda_handler(event, context):
    # Log the received event
    print(json.dumps(event))

    # Extract bucket name and object key from the S3 event
    try:
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            # Start the Step Functions state machine execution
            response = sfn_client.start_execution(
                stateMachineArn=os.environ['STT_WORKFLOW_ARN'],
                input=json.dumps({
                    'bucket': bucket,
                    'key': key
                })
            )
            print(f"Started execution: {response['executionArn']}")
    except KeyError as e:
        print(f"KeyError: {e}")
        raise e
    except Exception as e:
        print(f"Exception: {e}")
        raise e