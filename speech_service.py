# speech_service.py
import os
import shutil
import tempfile
from pydub import AudioSegment
from pydub.silence import split_on_silence
from google.cloud import speech
from google.oauth2 import service_account
from config import settings
from io import BytesIO 

class SpeechServiceError(Exception):
    """Custom exception for speech service errors."""
    pass

# Initialize the Google Speech Client
try:
    service_account_info = {
        "type": settings.GOOGLE_TYPE,
        "project_id": settings.GOOGLE_PROJECT_ID,
        "private_key_id": settings.GOOGLE_PRIVATE_KEY_ID,
        "private_key": settings.GOOGLE_PRIVATE_KEY.replace('\\n', '\n'),
        "client_email": settings.GOOGLE_CLIENT_EMAIL,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": settings.GOOGLE_CLIENT_X509_CERT_URL,
        "universe_domain": settings.GOOGLE_UNIVERSE_DOMAIN
    }
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    speech_client = speech.SpeechClient(credentials=credentials)
except Exception as e:
    print(f"Warning: Failed to initialize Google Speech client: {e}")
    speech_client = None

# <<< CHANGE: The function now requires the actual sample rate instead of guessing.
def _get_audio_config(file_path: str, sample_rate: int) -> speech.RecognitionConfig:
    """Gets the appropriate audio configuration based on file extension and actual sample rate."""
    file_ext = os.path.splitext(file_path)[1].lower().strip('.')
    
    encoding_map = {
        'wav': speech.RecognitionConfig.AudioEncoding.LINEAR16,
        'flac': speech.RecognitionConfig.AudioEncoding.FLAC,
        'webm': speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        'opus': speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        'mp3': speech.RecognitionConfig.AudioEncoding.MP3,
        'm4a': speech.RecognitionConfig.AudioEncoding.MP3,
    }
    encoding = encoding_map.get(file_ext, speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED)

    return speech.RecognitionConfig(
        encoding=encoding,
        sample_rate_hertz=sample_rate,  # <<< CHANGE: Use the provided, correct sample rate.
        language_code="en-US",
        enable_automatic_punctuation=True,
        model="latest_long",
        use_enhanced=True
    )

def _process_response(response) -> str:
    """Processes Google Speech response into a single transcript string."""
    return " ".join(
        [result.alternatives[0].transcript for result in response.results if result.alternatives]
    ).strip()

def transcribe_audio(file_path: str) -> str:
    """Transcribes an audio file, automatically handling long files."""
    if not speech_client:
        raise SpeechServiceError("Speech recognition service not available.")

    try:
        audio = AudioSegment.from_file(file_path)
        # <<< CHANGE: Get the actual sample rate from the pydub object.
        actual_sample_rate = audio.frame_rate

        if len(audio) > 60000:  # Use chunking for files > 60 seconds
            # <<< CHANGE: Pass the full audio object to the long audio handler.
            return _transcribe_long_audio(audio)
        else:
            # <<< CHANGE: Pass the correct sample rate to the short audio handler.
            return _transcribe_short_audio(file_path, actual_sample_rate)
    except Exception as e:
        raise SpeechServiceError(f"Transcription failed: {str(e)}")

def _transcribe_short_audio(file_path: str, sample_rate: int) -> str:
    """Transcribes audio files shorter than 60 seconds, ensuring mono channel."""
    
    # --- START OF FIX ---
    # Load the audio segment from the given path
    audio_segment = AudioSegment.from_file(file_path)

    # Google's API requires mono audio. Convert if it has more than one channel.
    if audio_segment.channels > 1:
        audio_segment = audio_segment.set_channels(1)
    
    # Export the (now guaranteed mono) audio to an in-memory buffer to get its byte content
    with BytesIO() as buffer:
        audio_segment.export(buffer, format="wav")
        content = buffer.getvalue()
    # --- END OF FIX ---

    # The original code read bytes from the file on disk.
    # We now use our in-memory `content` which is guaranteed to be mono.
    audio = speech.RecognitionAudio(content=content)
    
    # The config part remains the same. The sample rate is already correct from the previous fix.
    config = _get_audio_config(file_path, sample_rate)
    response = speech_client.recognize(config=config, audio=audio)
    return _process_response(response)

def _transcribe_long_audio(audio: AudioSegment) -> str:
    """Transcribes long audio files by splitting them into chunks."""
    # <<< CHANGE: Get the sample rate from the main audio object.
    sample_rate = audio.frame_rate
    
    chunks = split_on_silence(
        audio, min_silence_len=500, silence_thresh=-40, keep_silence=200
    )
    if not chunks: # If no silence, split manually
        chunks = [audio[i:i + 55000] for i in range(0, len(audio), 55000)] # Use 55s chunks

    transcripts = []
    temp_dir = tempfile.mkdtemp()
    try:
        for i, chunk in enumerate(chunks):
            # Skip very short chunks that result from splitting
            if len(chunk) < 250: continue
            
            chunk_file = os.path.join(temp_dir, f"chunk_{i}.wav")
            # Export the chunk as a WAV file. It will retain the original sample rate.
            chunk.export(chunk_file, format="wav")

            try:
                # <<< CHANGE: Pass the correct sample rate when transcribing the chunk.
                transcripts.append(_transcribe_short_audio(chunk_file, sample_rate))
            except Exception as e:
                # This warning is now more useful if an error still occurs.
                print(f"Warning: Could not transcribe chunk {i} ({len(chunk)}ms): {e}")
                continue
    finally:
        shutil.rmtree(temp_dir)
    
    return " ".join(transcripts).strip()