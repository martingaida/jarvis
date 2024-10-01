from dotenv import load_dotenv
import json
import boto3
import re
import os
import time
from botocore.exceptions import ClientError
from pathlib import Path
from urllib.parse import parse_qs
from datetime import datetime
from urllib.parse import urlparse

# Load the .env file from the parent directory
root_dir = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=root_dir / ".env")

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def create_response(status_code, body):
    return {
        'statusCode': status_code,
        'body': json.dumps(body if body else {}),  # Return an empty object if body is None
    }

def lambda_handler(event, context):
    try:
        # Log incoming event for debugging
        print((json.dumps))

        # Check the HTTP method from the requestContext
        http_method = event['requestContext']['http']['method']
        
        # Handle OPTIONS request for CORS
        if http_method == 'OPTIONS':
            return create_response(200, {
                'status': 'OK',
                'message': 'CORS preflight request'
            })
        
        # Handle GET request (assuming this is how status is checked)
        if http_method == 'GET':
            query_string_parameters = event.get('queryStringParameters', {})

            if query_string_parameters and 'fileName' in query_string_parameters:
                file_name = query_string_parameters['fileName']
                return handle_transcription_status(file_name)
            else:
                return create_response(400, {
                    'status': 'ERROR',
                    'result': None,
                    'error': 'Missing fileName parameter'
                })
        else:
            return create_response(405, {
                'status': 'ERROR',
                'result': None,
                'error': 'Method Not Allowed'
            })
    
    except Exception as e:
        print(f"Unexpected error in lambda_handler: {str(e)}")
        return create_response(500, {
            'status': 'ERROR',
            'result': None,
            'error': f"Error: {str(e)}"
        })
    

def get_transcript_content(transcript_uri, max_attempts=10, delay=30):
    attempt = 0
    # Parse the S3 URL
    parsed_uri = urlparse(transcript_uri)
    bucket = parsed_uri.path.split('/')[1]
    key = '/'.join(parsed_uri.path.split('/')[2:]).replace('.json', '_enhanced.json')
    print(f"Attempt {attempt}/{max_attempts}: Accessing S3 bucket: {bucket}, key: {key}")
    
    while attempt < max_attempts:
        attempt += 1
        try:
            # Get the transcript file from S3
            s3_response = s3.get_object(Bucket=bucket, Key=key)
            transcript_content = s3_response['Body'].read().decode('utf-8')
            print(f"Transcript content retrieved successfully on attempt {attempt}/{max_attempts}")
            return transcript_content
        except Exception as e:
            print(f"Attempt {attempt}/{max_attempts} failed: {str(e)}")
            if attempt < max_attempts:
                print(f"Waiting {delay} seconds before next attempt...")
                time.sleep(delay)
            else:
                print("All attempts to retrieve transcript content have failed")
                return None


def handle_transcription_status(job_name):
    try:
        job_name = f'stt-{job_name}'
        print(f"Checking transcription status for job: {job_name}")
        max_attempts = 10
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            try:
                response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
                print(f"Transcribe API response: {json.dumps(response, default=json_serial)}")
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                print(f"Job status: {status} (Attempt {attempt}/{max_attempts})")

                if status == 'COMPLETED':
                    transcript_uri = response['TranscriptionJob']['Transcript'].get('TranscriptFileUri')
                    print(f'URI: {transcript_uri}')

                    if not transcript_uri:
                        raise ValueError("TranscriptFileUri not found in completed job")

                    transcript_content = get_transcript_content(transcript_uri)
                    if transcript_content is None:
                        return create_response(500, {
                            'status': 'FAILED',
                            'result': None,
                            'error': 'Failed to retrieve transcript content after multiple attempts'
                        })
                    
                    return create_response(200, {
                        'status': 'COMPLETED',
                        'result': json.loads(transcript_content),
                        'error': None
                    })
                elif status in ['IN_PROGRESS', 'QUEUED']:
                    if attempt < max_attempts:
                        print(f"Job still in progress. Waiting for 30 seconds before next attempt...")
                        time.sleep(30)
                    else:
                        return create_response(200, {
                            'status': 'IN_PROGRESS',
                            'result': None,
                            'error': None
                        })
                else:
                    return create_response(200, {
                        'status': 'FAILED',
                        'result': None,
                        'error': f'Transcription failed with status: {status}'
                    })
                
            except (transcribe.exceptions.BadRequestException, transcribe.exceptions.NotFoundException):
                if attempt < max_attempts:
                    print(f"Transcription job '{job_name}' not found. Retrying in 30 seconds...")
                    time.sleep(30)
                else:
                    print(f"Transcription job '{job_name}' not found after {max_attempts} attempts")
                    return create_response(404, {
                        'status': 'ERROR',
                        'result': None,
                        'error': f'Transcription job not found: {job_name}'
                    })

    except ClientError as e:
        print(f"AWS client error: {str(e)}")
        return create_response(500, {
            'status': 'ERROR',
            'result': None,
            'error': f'AWS client error: {str(e)}'
        })
    except Exception as e:
        print(f"Unexpected error in handle_transcription_status: {str(e)}")
        return create_response(500, {
            'status': 'ERROR',
            'result': None,
            'error': f"Unexpected error: {str(e)}"
        })