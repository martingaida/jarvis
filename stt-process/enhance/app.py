import openai
import os

openai.api_key = os.environ['OPENAI_API_KEY']

def lambda_handler(event, context):
    # Enhance the transcript using OpenAI
    enhanced_transcript = enhance_with_openai(event['transcript'])
    
    return {
        'enhancedTranscript': enhanced_transcript,
        'speakers': event['speakers']
    }

def enhance_with_openai(transcript):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a legal transcription assistant. Enhance the following transcript by identifying speaker roles and legal terminology."},
            {"role": "user", "content": transcript}
        ]
    )
    return response.choices[0].message['content']