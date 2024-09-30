from openai import OpenAI, OpenAIError
from urllib.parse import urlparse
import boto3
import json
import os

# Initialize OpenAI API key from environment variable
s3 = boto3.client('s3')

# Set up OpenAI client
client = OpenAI()

MAX_TOKENS = 15000  # Define a limit to keep the token count well below the GPT model limit

def lambda_handler(event, context):
    try:
        # Log the incoming event
        print(f"Received event: {json.dumps(event)}")
        
        # Parse S3 URI to get the transcript
        bucket, key = event['bucket'], event['key']
                
        # Fetch the transcript file from S3
        transcript_obj = s3.get_object(Bucket=bucket, Key=key)
        transcript = json.loads(transcript_obj['Body'].read().decode('utf-8'))
        
        # Split the transcript into smaller chunks if necessary
        transcript_chunks = split_transcript_into_batches(transcript, MAX_TOKENS)

        # Process each chunk using GPT-4 Turbo for enhancing the segments
        enhanced_chunks = []
        for chunk in transcript_chunks:
            enhanced_chunk = enhance_with_openai(chunk)
            if enhanced_chunk:
                enhanced_chunks.append(enhanced_chunk)
            else:
                print(f"Warning: enhance_with_openai returned None for chunk: {chunk}")
        
        if not enhanced_chunks:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'No valid enhanced chunks were returned'})
            }
        
        # Combine the processed chunks into a single transcript
        combined_transcript = combine_enhanced_chunks(enhanced_chunks)

        # Perform NER on the entire combined transcript
        enhanced_transcript_with_ner = perform_ner_on_transcript(combined_transcript)
        
        if not enhanced_transcript_with_ner:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'NER process failed'})
            }
        
        enhanced_transcript_with_ner['s3'] = {
            'transcriptionOutputBucket': bucket, 
            'transcriptionJobName': key
        }

        return {
            'statusCode': 200,
            'body': json.dumps(enhanced_transcript_with_ner)  # Return JSON serializable output
        }
    
    except Exception as e:
        raise
    

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
        ]
    }}
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
            max_tokens=MAX_TOKENS,
            temperature=0
        )

        # Add logging to check the raw response
        print(f"Raw completion response: {completion}")

        # Check if the response content exists
        if not completion or not completion.choices:
            print("Warning: OpenAI API returned empty or invalid response.")
            return None

        # Extract the response text from the first choice and clean it
        response_text = completion.choices[0].message.content.strip()

        # Log the extracted response text
        print(f"Extracted response content: {response_text}")

        # Remove backticks and language indicators like ```json
        if response_text.startswith("```"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()

        # Parse the cleaned response text as JSON
        response_json = json.loads(response_text)

        return response_json
    
    except OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None
    except (IndexError, ValueError) as e:
        print(f"Unexpected response structure: {e}")
        return None


def perform_ner_on_transcript(transcript):
    """
    Enhances the entire transcript with Named Entity Recognition using GPT-4 Turbo.
    """
    prompt = f"""
    Perform Named Entity Recognition (NER) on the following transcript. Return the transcript with the identified entities categorized into the following categories:
    {{
        "transcript": "The entire transcript as a single string.",
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
    The transcript is:
    {transcript['transcript']}
    """
    
    try:
        # Make the API call to OpenAI's GPT-4 Turbo model
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You are a legal transcription assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=MAX_TOKENS,
            temperature=0
        )
        
        # Add logging to check the raw response
        print(f"Raw NER completion response: {completion}")

        # Check if the response content exists
        if not completion or not completion.choices:
            print("Warning: OpenAI API returned empty or invalid response for NER.")
            return None

        # Extract the response text from the first choice and clean it
        response_text = completion.choices[0].message.content.strip()

        # Log the extracted response text
        print(f"Extracted NER response content: {response_text}")

        # Remove backticks and language indicators like ```json
        if response_text.startswith("```"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()

        # Parse the cleaned response text as JSON
        response_json = json.loads(response_text)

        # Add identified entities to the transcript and return it
        transcript['entities'] = response_json.get('entities', {})

        return transcript
    
    except OpenAIError as e:
        print(f"OpenAI API error during NER: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON parsing error during NER: {e}")
        return None
    except (IndexError, ValueError) as e:
        print(f"Unexpected response structure during NER: {e}")
        return None



def combine_enhanced_chunks(chunks):
    """
    Combines multiple chunks of enhanced transcripts into a single enhanced transcript.
    """
    combined_transcript = ""
    combined_segments = []

    for chunk in chunks:
        combined_transcript += chunk['transcript'] + " "  # Combine the transcript text
        combined_segments.extend(chunk['segments'])       # Merge all segments into one list

    # Return the combined transcript with segments, ready for further NER processing
    return {
        "transcript": combined_transcript.strip(),  # Remove extra spaces
        "segments": combined_segments
    }