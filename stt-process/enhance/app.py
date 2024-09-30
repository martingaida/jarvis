from openai import OpenAI, OpenAIError
from urllib.parse import urlparse
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
import boto3
import json
import os

# Initialize OpenAI API key from environment variable
s3 = boto3.client('s3')

# Load the .env file from the parent directory
root_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=root_dir / ".env")

# Set up Open AI client
client = OpenAI()

class Segment(BaseModel):
    timestamp: str
    speaker: str
    text: str

class EnhancedTranscript(BaseModel):
    transcript: str
    segments: List[Segment]


def lambda_handler(event, context):
    try:
        # Parse S3 URI to get the transcript
        transcript_bucket, transcript_key = parse_s3_uri(event['transcriptS3Uri'])
        
        # Fetch the transcript file from S3
        transcript_obj = s3.get_object(Bucket=transcript_bucket, Key=transcript_key)
        transcript = json.loads(transcript_obj['Body'].read().decode('utf-8'))
        
        # Enhance the transcript using GPT-4 Turbo
        enhanced_transcript = enhance_with_openai(transcript)
        
        return enhanced_transcript
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def enhance_with_openai(transcript):
    # Prepare the prompt for GPT-4 Turbo to format the transcript as required
    prompt = f"""
    You are a legal transcription assistant. Format the following transcript into a JSON object with the following structure:
    {{
      "transcript": "The entire transcript as a single string.",
      "segments": [
        {{
          "timestamp": "timestamp for when the speaker starts talking",
          "speaker": "name or label of the speaker (if unknown, use 'Speaker X')",
          "text": "The actual speech text from the speaker"
        }}
      ]
    }}
    The transcript is:
    {json.dumps(transcript)}
    """
    
    try:
        # Make the API call to OpenAI's GPT-4 Turbo model
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You are a legal transcription assistant."},
                {"role": "user", "content": prompt}
            ],
            response_format=EnhancedTranscript,
        )
        
        # Extract the JSON output from the response
        response = json.loads(completion.choices[0].message.content)
        result = EnhancedTranscript(**response)
        
        return result
    
    except OpenAIError as e:
        print(f"OpenAI API error: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        raise
    except (IndexError, ValueError) as e:
        print(f"Unexpected response structure: {e}")
        raise

def parse_s3_uri(s3_uri):
    """Parses an S3 URI to extract the bucket and key."""
    parsed_url = urlparse(s3_uri)
    path_parts = parsed_url.path.lstrip('/').split('/', 1)
    bucket = path_parts[0]
    key = path_parts[1] if len(path_parts) > 1 else ''
    return bucket, key
