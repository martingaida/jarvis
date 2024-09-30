import boto3
import json
import uuid
from urllib.parse import urlparse, parse_qs
from datetime import datetime

def lambda_handler(event, context):
    transcribe = boto3.client('transcribe')
    s3 = boto3.client('s3')

    try:
        if 'transcriptionJobName' not in event:
            
            if 'bucket' not in event or 'key' not in event:
                raise Exception('Missing config')
            
            # Generate the base job name
            base_job_name = f"stt-{event['key'].split('/')[-1]}"
            job_name = base_job_name

            try:
                # Try to start a new transcription job with the base name
                response = transcribe.start_transcription_job(
                    TranscriptionJobName=job_name,
                    Media={'MediaFileUri': f"s3://{event['bucket']}/{event['key']}"},
                    MediaFormat='mp3',  # Adjust based on your audio format
                    LanguageCode='en-US',
                    OutputBucketName='ja-stt-transcription-outputs',
                    Settings={
                        'ShowSpeakerLabels': True,
                        'MaxSpeakerLabels': 10
                    }
                )
            except transcribe.exceptions.ConflictException:
                # If the job name already exists, check its status
                existing_job = transcribe.get_transcription_job(TranscriptionJobName=job_name)
                status = existing_job['TranscriptionJob']['TranscriptionJobStatus']
                
                if status not in ['COMPLETED', 'FAILED']:
                    # If the job is still pending or in progress, create a unique job name
                    unique_id = datetime.now().strftime("%Y%m%d%H%M%S") + "-" + str(uuid.uuid4())[:8]
                    job_name = f"{base_job_name}-{unique_id}"

                    # Start a new transcription job with the unique name
                    response = transcribe.start_transcription_job(
                        TranscriptionJobName=job_name,
                        Media={'MediaFileUri': f"s3://{event['bucket']}/{event['key']}"},
                        MediaFormat='m4a',
                        LanguageCode='en-US',
                        OutputBucketName='ja-stt-transcription-outputs',
                        Settings={
                            'ShowSpeakerLabels': True,
                            'MaxSpeakerLabels': 10
                        }
                    )
                else:
                    # If the existing job is completed or failed, delete it and start a new one with the base name
                    transcribe.delete_transcription_job(TranscriptionJobName=job_name)
                    response = transcribe.start_transcription_job(
                        TranscriptionJobName=job_name,
                        Media={'MediaFileUri': f"s3://{event['bucket']}/{event['key']}"},
                        MediaFormat='m4a',
                        LanguageCode='en-US',
                        OutputBucketName='ja-stt-transcription-outputs',
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
                # Generate the S3 key for the transcript
                output_bucket = 'ja-stt-transcription-outputs'
                output_key = f"transcripts/{job_name}.json"
                
                return {
                    'transcriptionJobName': job_name,
                    'transcriptionJobStatus': status,
                    'transcriptS3Uri': f"s3://{output_bucket}/{output_key}"
                }
            else:
                return {
                    'transcriptionJobName': job_name,
                    'transcriptionJobStatus': status
                }

    except Exception as e:
        print(f"Exception: {e}")
        raise e