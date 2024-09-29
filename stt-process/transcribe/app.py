import boto3
import json

def lambda_handler(event, context):
    transcribe = boto3.client('transcribe')
    s3 = boto3.client('s3')
    
    if 'transcriptionJobName' not in event:
        # Start a new transcription job
        job_name = f"LegalTranscription-{event['key'].split('/')[-1]}"
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
            transcript_bucket, transcript_key = transcript_uri.replace("s3://", "").split("/", 1)
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