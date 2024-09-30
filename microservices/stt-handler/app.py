import json

def lambda_handler(event, context):
    if 'body' in event:
        try:
            body = json.loads(event['body'])

            return {
                'statusCode': 200,
                'body': json.dumps(body)
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