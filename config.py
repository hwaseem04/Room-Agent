import os
from pathlib import Path

def load_env_file(env_path: Path):
    if not env_path.exists():
        return
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                value = value.strip()
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                os.environ[key.strip()] = value

# Load environment variables from .env file
load_env_file(Path(__file__).parent / ".env")

class Config:
    # Project Root
    ROOT_DIR = Path(__file__).parent.absolute()
    
    # Data Directories
    DATA_DIR = ROOT_DIR / "data"
    FACES_DIR = ROOT_DIR / "faces"
    EMBEDDINGS_DIR = FACES_DIR / "embeddings"
    MODELS_DIR = ROOT_DIR / "models"
    VOSK_MODEL_PATH = MODELS_DIR / "vosk-model"
    
    # File Paths
    VISITOR_LOG_PATH = DATA_DIR / "visitor_log.txt"
    DB_PATH = DATA_DIR / "item_log.db"
    ITEM_FRAMES_DIR = DATA_DIR / "item_frames"
    
    # Camera
    CAMERA_INDEX = 0
    CAMERA_FRAME_WIDTH = 640  # Default, can be adjusted
    CAMERA_FRAME_HEIGHT = 480
    
    # Face Recognition
    FACE_RECOG_THRESHOLD = 0.45
    
    # Speech & Audio
    PAUSE_THRESHOLD = 1.2
    
    # API Keys
    AUDIO_OUTPUT = "default"  # Options: "default", "openai"
    STT_PROVIDER = "vosk"     # Options: "vosk", "google", "openai"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Ensure directories exist
    @classmethod
    def ensure_directories(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.ITEM_FRAMES_DIR.mkdir(parents=True, exist_ok=True)
