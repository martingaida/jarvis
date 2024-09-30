import json
import boto3

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    try:
        # Parse the body from the event, since it is a JSON string
        body = json.loads(event['body'])  # Parse the 'body' field as JSON

        # Extract the transcript and segments from the parsed body
        enhanced_transcript = body.get('transcript')  # Full transcript text
        segments = body.get('segments')  # List of segments

        # Validate that the required fields exist
        if not enhanced_transcript:
            raise KeyError("Missing 'transcript' in body")
        if not segments:
            raise KeyError("Missing 'segments' in body")
        
        # Combine the enhanced transcript with speaker information
        final_result = {
            'transcript': enhanced_transcript,
            'speakers': segments
        }

        # Save to S3
        output_bucket = event.get('transcriptionOutputBucket')
        output_key = f"transcription_{event.get('transcriptionJobName')}.json"
        
        # Validate bucket and key
        if not output_bucket or not output_key:
            raise KeyError("Missing 'transcriptionOutputBucket' or 'transcriptionJobName' in event data")
        
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
    
    except KeyError as e:
        print(f"KeyError: {e}")
        return {
            'status': 'error',
            'message': f"Missing key in event: {e}"
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }