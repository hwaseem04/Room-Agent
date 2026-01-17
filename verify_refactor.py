
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Importing config...")
    from config import Config
    print("Importing logger...")
    from logger import logger
    print("Importing utils...")
    from utils import load_known_faces
    print("Importing tool_calling...")
    from tool_calling import get_tools
    print("Importing speech modules...")
    from speech.listener import speech_listener
    from speech.handler import handle_speech_input
    print("Importing agent...")
    from agent import VideoAgent
    print("All modules imported successfully.")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)
