
import os
import sqlite3
import numpy as np
import time
from pathlib import Path
from typing import Dict, Tuple, Any

from config import Config
from logger import logger

def load_known_faces(embeddings_folder: Path) -> Dict[str, np.ndarray]:
    """
    Loads face embeddings from the specified folder.
    """
    known_faces = {}
    if not embeddings_folder.exists():
        logger.warning(f"Embeddings folder not found: {embeddings_folder}")
        return known_faces

    for file_path in embeddings_folder.glob("*_embedding.npy"):
        try:
            # Extract name from filename
            name = file_path.stem.replace("_embedding", "")
            # Load embedding
            embedding = np.load(str(file_path))
            known_faces[name] = embedding
            logger.debug(f"Loaded face embedding for: {name}")
        except Exception as e:
            logger.error(f"Failed to load embedding {file_path}: {e}")
            
    logger.info(f"Loaded {len(known_faces)} known faces.")
    return known_faces


def init_item_db(db_path: Path = Config.DB_PATH) -> None:
    """
    Initializes the SQLite database for item logging.
    """
    try:
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(str(db_path)) as conn:
            c = conn.cursor()
            c.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person TEXT,
                item TEXT,
                place TEXT,
                timestamp TEXT,
                image_path TEXT
            )
            """)
            conn.commit()
        logger.info(f"Initialized item database at {db_path}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


def compute_latency(start_time: float, end_time: float, task: str = "", precision: int = 3) -> float:
    """
    Computes and logs the latency of a task.
    """
    latency = round(end_time - start_time, precision)
    logger.info(f"{task} Latency: {latency} seconds")
    return latency
