
import subprocess
from pathlib import Path
from openai import OpenAI
from logger import logger
from config import Config

# Initialize OpenAI client
try:
    client = OpenAI(api_key=Config.OPENAI_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client in notifier: {e}")
    client = None

def notify(message: str) -> None:
    """
    Logs the message and speaks it using OpenAI TTS (blocking).
    Falls back to system 'say' command if OpenAI fails.
    """
    logger.info(f"[NOTIFIER] {message}")
    
    if not message.strip():
        return

    # Try OpenAI TTS first if selected
    if Config.AUDIO_OUTPUT == "openai" and client:
        try:
            speech_file_path = Path(__file__).parent / "response.mp3"
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=message
            )
            
            # Save to file
            response.stream_to_file(speech_file_path)
            
            # Play using afplay (blocking)
            subprocess.run(['afplay', str(speech_file_path)], check=False)
            
            # Cleanup
            if speech_file_path.exists():
                speech_file_path.unlink()
            return

        except Exception as e:
            logger.error(f"OpenAI TTS failed: {e}. Falling back to system TTS.")

    # Fallback or default to system TTS
    try:
        subprocess.run(['say', '-v', 'Samantha', message], check=False)
    except Exception as e:
        logger.error(f"System TTS failed: {e}")
