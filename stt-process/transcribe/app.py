import boto3
import json

def lambda_handler(event, context):
    transcribe = boto3.client('transcribe')
    s3 = boto3.client('s3')
    
    try:
        if 'transcriptionJobName' not in event:
            
            if 'bucket' not in event or 'key' not in event:
                raise Exception('Missing config')
            
            # Start a new transcription job
            job_name = f"stt-{event['key'].split('/')[-1]}"
            try:
                response = transcribe.start_transcription_job(
                    TranscriptionJobName=job_name,
                    Media={'MediaFileUri': f"s3://{event['bucket']}/{event['key']}"},
                    MediaFormat='mp3',  # Adjust based on your audio format
                    LanguageCode='en-US',
                    Settings={
                        'ShowSpeakerLabels': True,
                        'MaxSpeakerLabels': 10
                    }
                )
            except transcribe.exceptions.ConflictException:
                # If the job name already exists, delete the existing job and start a new one
                transcribe.delete_transcription_job(TranscriptionJobName=job_name)
                response = transcribe.start_transcription_job(
                    TranscriptionJobName=job_name,
                    Media={'MediaFileUri': f"s3://{event['bucket']}/{event['key']}"},
                    MediaFormat='mp3',  # Adjust based on your audio format
                    LanguageCode='en-US',
                    Settings={
                        'ShowSpeakerLabels': True,
                        'MaxSpeakerLabels': 10
                    }
                )
            return {'transcriptionJobName': job_name, 'transcriptionJobStatus': 'IN_PROGRESS'}
        
        else:
            # Check the status of an existing job
            job_name = event['transcriptionJobName']
            response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                # Fetch the transcript
                transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                transcript_bucket, transcript_key = parse_s3_uri(transcript_uri)
                transcript_obj = s3.get_object(Bucket=transcript_bucket, Key=transcript_key)
                transcript = json.loads(transcript_obj['Body'].read().decode('utf-8'))
                
                return {
                    'transcriptionJobName': job_name,
                    'transcriptionJobStatus': status,
                    'transcript': transcript
                }
            else:
                return {
                    'transcriptionJobName': job_name,
                    'transcriptionJobStatus': status
                }
            
    except Exception as e:
        print(f"Exception: {e}")
        raise e

def parse_s3_uri(s3_uri):
    """Parse an S3 URI into bucket and key."""
    if s3_uri.startswith("s3://"):
        s3_uri = s3_uri[5:]
    bucket, key = s3_uri.split("/", 1)
    return bucket, key