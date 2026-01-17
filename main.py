
import warnings
# Suppress specific warnings if needed, or rely on logger configuration
warnings.filterwarnings("ignore")

import sys
from agent import VideoAgent
from logger import setup_logger

import argparse
from config import Config

def parse_arguments():
    parser = argparse.ArgumentParser(description="Video Room Agent")
    parser.add_argument(
        "--audio_output", 
        choices=["default", "openai"], 
        default="default",
        help="Select audio output method: 'default' (System TTS) or 'openai' (OpenAI TTS)."
    )
    parser.add_argument(
        "--audio_input",
        choices=["vosk", "google", "openai"],
        default="vosk",
        help="Select speech-to-text provider: 'vosk' (Offline), 'google' (Online Free), or 'openai' (Whisper API)."
    )
    return parser.parse_args()

def main():
    # Setup global logger
    logger = setup_logger()
    
    # Parse CLI args
    args = parse_arguments()
    Config.AUDIO_OUTPUT = args.audio_output
    Config.STT_PROVIDER = args.audio_input
    logger.info(f"Audio Output mode set to: {Config.AUDIO_OUTPUT}")
    logger.info(f"STT Provider set to: {Config.STT_PROVIDER}")
    
    try:
        agent = VideoAgent()
        agent.start()
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
