
import os
import requests
import zipfile
from pathlib import Path
from tqdm import tqdm

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_ZIP = "vosk-model-small-en-us-0.15.zip"
MODEL_DIR = Path(__file__).parent / "models"

def download_file(url, filename):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024
    
    with open(filename, "wb") as f, tqdm(
        desc=filename,
        total=total_size,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(block_size):
            size = f.write(data)
            bar.update(size)

def main():
    if not MODEL_DIR.exists():
        MODEL_DIR.mkdir()

    zip_path = MODEL_DIR / MODEL_ZIP
    
    # Download
    if not zip_path.exists():
        print(f"Downloading model from {MODEL_URL}...")
        download_file(MODEL_URL, str(zip_path))
    else:
        print("Model zip already exists.")

    # Extract
    print("Extracting model...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(MODEL_DIR)
        
    extracted_folder = MODEL_DIR / "vosk-model-small-en-us-0.15"
    target_folder = MODEL_DIR / "vosk-model"
    
    if target_folder.exists():
        print("Cleaning up old model directory...")
        import shutil
        shutil.rmtree(target_folder)
        
    extracted_folder.rename(target_folder)
    print(f"Model ready at: {target_folder}")

if __name__ == "__main__":
    main()
