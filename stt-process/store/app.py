import json
import boto3

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    # Combine the enhanced transcript with speaker information
    final_result = {
        'transcript': event['enhancedTranscript'],
        'speakers': event['speakers']
    }
    
    # Save to S3
    output_bucket = event['transcriptionOutputBucket']
    output_key = f"transcription_{event['transcriptionJobName']}.json"
    
    s3.put_object(
        Bucket=output_bucket,
        Key=output_key,
        Body=json.dumps(final_result),
        ContentType='application/json'
    )
    
    return {
        'status': 'success',
        'outputLocation': f"s3://{output_bucket}/{output_key}"
    }