from openai import OpenAI, OpenAIError
from urllib.parse import urlparse
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict
import boto3
import json
import os
import math

# Initialize OpenAI API key from environment variable
s3 = boto3.client('s3')

# Set up OpenAI client
client = OpenAI()

class Entity(BaseModel):
    type: str
    value: str

class Segment(BaseModel):
    timestamp: str
    speaker: str
    text: str

class EnhancedTranscript(BaseModel):
    transcript: str
    segments: List[Segment]
    entities: Dict[str, List[str]]

MAX_TOKENS = 50000  # Define a limit to keep the token count well below the GPT model limit

def lambda_handler(event, context):
    try:
        # Log the incoming event
        print(f"Received event: {json.dumps(event)}")
        
        # Parse S3 URI to get the transcript
        bucket, key = event['bucket'], event['key']
                
        # Fetch the transcript file from S3
        transcript_obj = s3.get_object(Bucket=bucket, Key=key)
        transcript = json.loads(transcript_obj['Body'].read().decode('utf-8'))
        
        # Split the transcript into smaller chunks
        transcript_chunks = split_transcript_into_batches(transcript, MAX_TOKENS)

        # Process each chunk using GPT-4 Turbo
        enhanced_chunks = [enhance_with_openai(chunk) for chunk in transcript_chunks]
        
        # Combine the processed chunks into a single enhanced transcript
        enhanced_transcript = combine_enhanced_chunks(enhanced_chunks)
        
        # Convert the Pydantic model to a dict to make it JSON serializable
        return {
            'statusCode': 200,
            'body': json.dumps(enhanced_transcript.dict())  # Use .dict() to make it JSON serializable
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def split_transcript_into_batches(transcript, max_tokens):
    """
    Splits the transcript into smaller chunks based on the max token limit.
    """
    segments = transcript['results']['speaker_labels']['segments']
    transcript_items = transcript['results']['items']
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for segment in segments:
        # Calculate segment token count using an approximation (word count)
        segment_text = get_text_for_segment(segment, transcript_items)
        segment_token_count = len(segment_text.split())
        
        if current_token_count + segment_token_count > max_tokens:
            # If adding this segment exceeds the token limit, start a new chunk
            chunks.append(current_chunk)
            current_chunk = []
            current_token_count = 0
        
        # Add the segment to the current chunk
        current_chunk.append({
            'timestamp': segment['start_time'],
            'speaker': segment['speaker_label'],
            'text': segment_text
        })
        current_token_count += segment_token_count
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def get_text_for_segment(segment, transcript_items):
    """
    Get the transcript text corresponding to a given speaker segment.
    """
    segment_text = []
    start_time = float(segment['start_time'])
    end_time = float(segment['end_time'])

    for item in transcript_items:
        if 'start_time' in item and start_time <= float(item['start_time']) <= end_time:
            if item['type'] == 'pronunciation' or item['type'] == 'punctuation':
                segment_text.append(item['alternatives'][0]['content'])

    return " ".join(segment_text)

def enhance_with_openai(transcript_chunk):
    """
    Enhances a chunk of the transcript using GPT-4 Turbo.
    """
    prompt = f"""
    You are a legal transcription assistant. Format the following transcript into a JSON object with the following structure:
    {{
        "transcript": "The entire transcript as a single string.",
        "segments": [
            {{
            "timestamp": "timestamp for when the speaker starts talking",
            "speaker": "best guess name or title label of the speaker (if unknown, use 'Speaker X')",
            "text": "The actual speech text from the speaker"
            }}
        ],
        "entities": {{
            "ATTORNEY": ["List of unique attorney names"],
            "PLAINTIFF": ["List of unique plaintiff names"],
            "DEFENDANT": ["List of unique defendant names"],
            "JUDGE": ["List of unique judge names"],
            "WITNESS": ["List of unique witness names"],
            "EXPERT": ["List of unique expert witness names"],
            "COMPANY": ["List of unique company names"],
            "CASE_NUMBER": ["List of unique case numbers"],
            "COURT": ["List of unique court names"],
            "DATE": ["List of unique relevant dates"],
            "LOCATION": ["List of unique relevant locations"],
            "STATUTE": ["List of unique statute references"],
            "EXHIBIT": ["List of unique exhibit references"],
            "LEGAL_TERM": ["List of unique legal terms or jargon"]
        }}
    }}
    Identify and categorize important entities such as attorney names, plaintiff names, company names, and case file numbers. Include these entities in the overall entities list, not in individual segments.
    The transcript is:
    {json.dumps(transcript_chunk)}
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

def combine_enhanced_chunks(chunks):
    """
    Combines multiple chunks of enhanced transcripts into a single enhanced transcript.
    """
    combined_transcript = ""
    combined_segments = []
    combined_entities = {
        "ATTORNEY": set(),
        "PLAINTIFF": set(),
        "DEFENDANT": set(),
        "JUDGE": set(),
        "WITNESS": set(),
        "EXPERT": set(),
        "COMPANY": set(),
        "CASE_NUMBER": set(),
        "COURT": set(),
        "DATE": set(),
        "LOCATION": set(),
        "STATUTE": set(),
        "EXHIBIT": set(),
        "LEGAL_TERM": set()
    }

    for chunk in chunks:
        combined_transcript += chunk.transcript + " "
        combined_segments.extend(chunk.segments)
        for entity_type, entities in chunk.entities.items():
            combined_entities[entity_type].update(entities)

    return EnhancedTranscript(
        transcript=combined_transcript.strip(),
        segments=combined_segments,
        entities={k: list(v) for k, v in combined_entities.items()}
    )