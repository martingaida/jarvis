import json
import boto3

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    # Extract bucket and key from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # You can add additional processing here if needed
    
    return {
        'bucket': bucket,
        'key': key
    }