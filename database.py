
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional
from logger import logger

class ItemDatabase:
    """
    Handles all interactions with the item logging database.
    """
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Creates the table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS item_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_name TEXT,
                        place_name TEXT,
                        image_path TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """)
                conn.commit()
            logger.info(f"Initialized item database at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def log_item(self, item_name: str, place_name: str, image_path: str, description: str = "") -> bool:
        """Logs an item's location."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO item_log (item_name, place_name, image_path, description) VALUES (?, ?, ?, ?)",
                    (item_name.lower(), place_name.lower(), str(image_path), description)
                )
                conn.commit()
            logger.info(f"Logged item '{item_name}' at '{place_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to log item: {e}")
            return False

    def delete_item(self, item_id: int) -> bool:
        """Deletes an item by ID and removes its image file."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Fetch image path before deletion
                cursor.execute("SELECT image_path FROM item_log WHERE id = ?", (item_id,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    image_path = Path(result[0])
                    if image_path.exists():
                        try:
                            image_path.unlink()
                            logger.info(f"Deleted image file: {image_path}")
                        except Exception as e:
                            logger.error(f"Failed to delete image file {image_path}: {e}")

                # Delete record
                cursor.execute("DELETE FROM item_log WHERE id = ?", (item_id,))
                conn.commit()
            logger.info(f"Deleted item with ID {item_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete item {item_id}: {e}")
            return False

    def search_items(self, query: str) -> List[Tuple]:
        """
        Smart search: Exact match -> Token match -> Recent items (fallback).
        Returns list of tuples: (id, item_name, place_name, timestamp, image_path)
        """
        query = query.lower().strip()
        
        # 1. Exact/Loose phrase match
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, item_name, place_name, timestamp, image_path FROM item_log WHERE item_name LIKE ? ORDER BY timestamp DESC",
                    (f"%{query}%",)
                )
                results = cursor.fetchall()
                if results:
                    return results
        except Exception as e:
            logger.error(f"Failed to search items (exact): {e}")

        # 2. Token match (any word matches)
        tokens = query.split()
        if len(tokens) > 1:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    conditions = " OR ".join(["item_name LIKE ?" for _ in tokens])
                    params = [f"%{t}%" for t in tokens]
                    
                    cursor.execute(
                        f"SELECT id, item_name, place_name, timestamp, image_path FROM item_log WHERE {conditions} ORDER BY timestamp DESC",
                        params
                    )
                    results = cursor.fetchall()
                    if results:
                        return results
            except Exception as e:
                logger.error(f"Failed to search items (tokens): {e}")

        # 3. Fallback to recent
        return self.get_recent_items()

    def get_recent_items(self, limit: int = 5) -> List[Tuple]:
        """Returns most recent items."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, item_name, place_name, timestamp, image_path FROM item_log ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to get recent items: {e}")
            return []

    def find_item(self, item_name: str) -> List[Tuple]:
        """Legacy alias for backward compatibility or simple exact search."""
        return self.search_items(item_name)

    def get_all_items(self) -> List[Tuple[str, str, str]]:
        """Returns all logged items."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT item_name, place_name, timestamp FROM item_log ORDER BY timestamp DESC")
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to retrieve all items: {e}")
            return []
