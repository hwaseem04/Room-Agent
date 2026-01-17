
import sys
import time
from config import Config
from logger import setup_logger

logger = setup_logger()

def check_model():
    logger.info(f"Checking Vosk model at: {Config.VOSK_MODEL_PATH}")
    if Config.VOSK_MODEL_PATH.exists():
        logger.info("✅ Vosk model found.")
        try:
            from vosk import Model
            model = Model(str(Config.VOSK_MODEL_PATH))
            logger.info("✅ Vosk model loaded successfully.")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load Vosk model: {e}")
            return False
    else:
        logger.error("❌ Vosk model NOT found.")
        return False

def check_tts():
    logger.info("Checking TTS (should be non-blocking)...")
    from notifier import notify
    start = time.time()
    notify("Audio check. One two three.")
    end = time.time()
    duration = end - start
    logger.info(f"TTS Call duration: {duration:.4f}s")
    
    if duration < 0.1:
        logger.info("✅ TTS is non-blocking.")
        return True
    else:
        logger.warning("⚠️ TTS might be blocking (call took too long).")
        return False

def main():
    if check_model() and check_tts():
        logger.info("All audio checks passed. You can run 'python main.py' now.")
    else:
        logger.error("Some checks failed.")

if __name__ == "__main__":
    main()
