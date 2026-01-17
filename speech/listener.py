import json
import pyaudio
import time
import speech_recognition as sr
import tempfile
import os
from queue import Queue
from threading import Event
from openai import OpenAI

from vosk import Model, KaldiRecognizer
from config import Config
from logger import logger

def speech_listener(audio_queue: Queue, pause_listener_event: Event):
    """
    Dispatches to the configured STT provider.
    """
    provider = Config.STT_PROVIDER
    logger.info(f"Starting Speech Listener with provider: {provider}")
    
    while True:
        try:
            if provider == "vosk":
                _listen_vosk(audio_queue, pause_listener_event)
            elif provider == "google":
                _listen_speech_recognition(audio_queue, pause_listener_event, engine="google")
            elif provider == "openai":
                _listen_speech_recognition(audio_queue, pause_listener_event, engine="openai")
            else:
                logger.error(f"Unknown STT provider: {provider}")
                break
        except Exception as e:
            logger.error(f"Listener crash in {provider}: {e}")
            time.sleep(2)

def _listen_vosk(audio_queue: Queue, pause_listener_event: Event):
    """
    Continuously listens using Vosk (offline STT).
    """
    if not Config.VOSK_MODEL_PATH.exists():
        logger.error(f"Vosk model not found at {Config.VOSK_MODEL_PATH}")
        return

    logger.info("Loading Vosk model... (this may take a moment)")
    try:
        model = Model(str(Config.VOSK_MODEL_PATH))
    except Exception as e:
        logger.error(f"Failed to load Vosk model: {e}")
        return

    # Audio Configuration
    samplerate = 16000
    recognizer = KaldiRecognizer(model, samplerate)
    
    p = pyaudio.PyAudio()
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=samplerate,
            input=True,
            frames_per_buffer=4000
        )
    except Exception as e:
        logger.error(f"Failed to open audio stream: {e}")
        return

    stream.start_stream()
    logger.info("Vosk Listener ready. Listening...")

    while True:
        if pause_listener_event.is_set():
            # Flush the buffer by reading and discarding data
            try:
                stream.read(4000, exception_on_overflow=False)
            except Exception:
                pass
            time.sleep(0.01) # Short sleep to prevent CPU spinning
            continue

        try:
            data = stream.read(4000, exception_on_overflow=False)
            if len(data) == 0:
                continue

            if recognizer.AcceptWaveform(data):
                result_json = recognizer.Result()
                result = json.loads(result_json)
                text = result.get("text", "")
                
                if text:
                    logger.info(f"Heard (Vosk): '{text}'")
                    audio_queue.put(text)
                    
        except Exception as e:
            logger.error(f"Vosk listener error: {e}")
            time.sleep(1)

def _listen_speech_recognition(audio_queue: Queue, pause_listener_event: Event, engine="google"):
    """
    Uses the speech_recognition library for Google or OpenAI Whisper.
    """
    r = sr.Recognizer()
    mic = sr.Microphone()
    
    # Optional: Initialize OpenAI client if needed
    client = None
    if engine == "openai":
        if not Config.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY missing for Whisper STT. Falling back to Google.")
            engine = "google"
        else:
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    logger.info(f"Initializing {engine.upper()} listener...")
    
    # Adjust for ambient noise once
    with mic as source:
        logger.info("Adjusting for ambient noise... (Please be quiet)")
        r.adjust_for_ambient_noise(source, duration=1.0)
        logger.info("Adjustment complete.")
        
    logger.info(f"{engine.upper()} Listener ready. Listening...")
    
    while True:
        if pause_listener_event.is_set():
            time.sleep(0.1)
            continue
            
        try:
            with mic as source:
                # Listen with a timeout to allow checking pause_event loop
                try:
                    audio = r.listen(source, timeout=1.0, phrase_time_limit=10.0)
                except sr.WaitTimeoutError:
                    continue 
                
                if pause_listener_event.is_set():
                    continue

                text = ""
                try:
                    if engine == "google":
                        text = r.recognize_google(audio)
                    elif engine == "openai" and client:
                        # OpenAI API implementation using temp file
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                            f.write(audio.get_wav_data())
                            tmp_filename = f.name
                            
                        try:
                            with open(tmp_filename, "rb") as audio_file:
                                 transcription = client.audio.transcriptions.create(
                                    model="whisper-1", 
                                    file=audio_file,
                                    prompt="Digital assistant request" # optional context
                                 )
                                 text = transcription.text
                        finally:
                            if os.path.exists(tmp_filename):
                                os.remove(tmp_filename)

                    if text:
                        logger.info(f"Heard ({engine}): '{text}'")
                        audio_queue.put(text)
                        
                except sr.UnknownValueError:
                    pass # unintelligible
                except sr.RequestError as e:
                    logger.error(f"STT Service Error ({engine}): {e}")
                    time.sleep(2)
                    
        except Exception as e:
            logger.error(f"Listener Loop Error ({engine}): {e}")
            time.sleep(1)
