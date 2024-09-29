from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI, OpenAIError
from pydub import AudioSegment
from pathlib import Path
from typing import List
import logging
import time
import os
import json
from openai.types.audio import TranscriptionVerbose
from pyannote.audio import Pipeline  # Import PyAnnote for diarization

#  Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load the .env file from the parent directory
microservices_root_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=microservices_root_dir / ".env")

# Set up OpenAI client
client = OpenAI()

class TranscriptionResponse(BaseModel):
    text: str
    confidence: float
    speakers: List[str] = []
    timestamps: List[dict] = []

def diarize_audio(audio_file_path: str) -> List[dict]:
    """
    Perform speaker diarization on the audio file using PyAnnote and return speaker segments.
    
    Args:
        audio_file_path (str): Path to the audio file to perform diarization.

    Returns:
        List[dict]: A list of speaker segments with start time, end time, and speaker label.
    """
    audio_file_path = audio_file_path.replace('m4a', 'wav')
    logger.info(f"Starting diarization for {audio_file_path}")

    # Hugging Face token for authentication
    HF_TOKEN = os.getenv("HF_AUTH_TOKEN")  
    
    if not HF_TOKEN:
        raise ValueError("Hugging Face token not found. Please set it as an environment variable 'HF_AUTH_TOKEN'.")

    # Authenticate and load the diarization pipeline
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1", use_auth_token=HF_TOKEN)
    diarization = pipeline(audio_file_path)

    speaker_segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segment = {
            "start": turn.start,
            "end": turn.end,
            "speaker": speaker
        }
        speaker_segments.append(segment)

    logger.info(f"Diarization complete. Speaker segments: {speaker_segments}")
    return speaker_segments


def transcribe_audio(audio_file_path: str) -> TranscriptionResponse:
    """
    Transcribe audio using OpenAI's Whisper model and align with PyAnnote speaker diarization.

    Args:
        audio_file_path (str): Path to the audio file to transcribe.

    Returns:
        TranscriptionResponse: A structured object containing the transcription,
        speaker identification, and timestamps.
    """

    # Check file size and split if necessary
    audio_file_size = os.path.getsize(audio_file_path) / (1024 * 1024)  # Size in MB
    if audio_file_size > 25:
        print(f"File size is {audio_file_size:.2f} MB, splitting audio...")
        split_audio(audio_file_path)
        return

    try:
        # Perform speaker diarization
        speaker_segments = diarize_audio(audio_file_path)

        # Custom legal vocabulary to prime the model
        legal_vocabulary = [
            "Affidavit", "Appeal", "Arraignment", "Bail", "Brief", "Claim", "Damages", "Defendant", "Deposition", 
            "Injunction", "Judgment", "Liability", "Motion", "Plaintiff", "Subpoena", "Tort", "Verdict", "Witness", 
            "Ad hoc", "Amicus curiae", "Bona fide", "De facto", "Habeas corpus", "Ipso facto", "Mens rea", 
            "Nolo contendere", "Per curiam", "Pro bono", "Res judicata", "Stare decisis", "Subpoena duces tecum", 
            "Ultra vires", "Venire", "Breach of contract", "Consideration", "Force majeure", "Indemnity", "Jurisdiction", 
            "Null and void", "Statute of limitations", "Voir dire", "Cross-examination", "Direct examination", 
            "Plea bargain", "Summary judgment", "Burden of proof", "Acquittal", "Alibi", "Conviction", "Double jeopardy", 
            "Exoneration"
        ]

        # Convert vocabulary list to a string for the prompt
        vocabulary_string = ", ".join(legal_vocabulary)

        # Custom legal-specific prompt
        prompt = f"""
        You are a highly accurate legal transcription assistant. Your task is to transcribe the following audio, capturing legal terminology and speaker roles. 
        Ensure you accurately transcribe legal terms such as {vocabulary_string}. Provide clear speaker identification (e.g., Attorney, Witness, Judge). 
        If the speaker's name or role is unclear, use numbered placeholders such as [unknown speaker 1], [unknown speaker 2], and so on. For any unclear audio, use markers such as [inaudible] or [unclear].
        """

        # Open the file and keep it open for the duration of the API call
        with open(audio_file_path, 'rb') as audio_file:
            # Send audio data to OpenAI's Whisper model
            transcription: TranscriptionVerbose = client.audio.transcriptions.create(
                model="whisper-1",  # Whisper model for speech-to-text
                file=audio_file,
                prompt=prompt,  # Legal-specific prompt with vocabulary
                response_format="verbose_json",  # Requesting detailed output with timestamps
                timestamp_granularities=["word"]  # Word-level timestamps
            )

        # Convert TranscriptionVerbose to a dictionary
        transcription_dict = transcription.model_dump()

        # Combine diarization results with transcription
        combined_results = combine_transcription_and_diarization(transcription_dict, speaker_segments)

        # Print the combined results
        print(json.dumps(combined_results, indent=2))

        # Construct and return the TranscriptionResponse
        return TranscriptionResponse(
            text=combined_results['text'],
            confidence=getattr(transcription, 'confidence', 1.0),
            speakers=combined_results['speakers'],
            timestamps=combined_results['timestamps']
        )

    except OpenAIError as e:
        print(f"OpenAI API error: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise


def combine_transcription_and_diarization(transcription, speaker_segments):
    """
    Combine transcription results with speaker diarization.

    Args:
        transcription (dict): The transcription output from OpenAI's Whisper model.
        speaker_segments (list): The diarization output from PyAnnote.

    Returns:
        dict: Combined transcription with speaker information.
    """
    word_segments = transcription['segments']
    combined_results = {'text': '', 'speakers': [], 'timestamps': []}

    for segment in word_segments:
        word_start = segment['start']
        word_end = segment['end']
        text = segment['text']
        
        # Find the corresponding speaker for each word segment based on the time
        speaker = next((s['speaker'] for s in speaker_segments if s['start'] <= word_start <= s['end']), "unknown speaker")

        combined_results['text'] += f"{speaker}: {text} "
        combined_results['speakers'].append(speaker)
        combined_results['timestamps'].append({
            'start': word_start,
            'end': word_end,
            'speaker': speaker,
            'text': text
        })

    return combined_results


def split_audio(audio_file_path):
    """
    Split audio file into 25 MB chunks using PyDub.
    """
    audio = AudioSegment.from_file(audio_file_path)
    chunk_length_ms = (25 * 1024 * 1024) // audio.frame_rate // audio.frame_width * 1000  # Approx. time for 25 MB
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

    for i, chunk in enumerate(chunks):
        chunk_file = f"chunk_{i}.mp3"
        chunk.export(chunk_file, format="mp3")
        print(f"Exported {chunk_file}, processing chunk...")
        transcribe_audio(chunk_file)


def handle_transcription_request(audio_file_path):
    try:
        start_time = time.time()
        final = transcribe_audio(audio_file_path)
        total_time = time.time() - start_time
        print(f'Total function runtime: {total_time:.2f} seconds')

        # Convert the final TranscriptionResponse to a dictionary
        final_dict = final.model_dump()

        # Create a filename based on the original audio file
        audio_file = Path(audio_file_path)
        json_filename = audio_file.with_suffix('.json')

        # Save the transcription as a JSON file
        with open(json_filename, 'w', encoding='utf-8') as json_file:
            json.dump(final_dict, json_file, ensure_ascii=False, indent=2)

        print(f"Transcription saved to {json_filename}")

        return {"transcription": final_dict, "file_path": str(json_filename)}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        audio_file_path = sys.argv[1]
        result = handle_transcription_request(audio_file_path)
        print("Transcription complete")
    else:
        print("Please provide an audio file path as an argument")