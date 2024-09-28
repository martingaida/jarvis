import json
import boto3
import os
from handlers import explain


def lambda_handler(event, context):
    if 'body' in event:
        try:
            body = json.loads(event['body'])
            text = body.get('text', '')

            # Process the text synchronously
            result = explain.generate_response(text)

            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request'})
        }