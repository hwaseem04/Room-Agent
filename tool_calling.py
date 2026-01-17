
import cv2
import time
from datetime import datetime
from threading import Event
from queue import Queue
from functools import partial
from typing import Optional, Type

from langchain.agents import Tool
from langchain.tools import StructuredTool
from langchain.pydantic_v1 import BaseModel, Field

from config import Config
from logger import logger
from database import ItemDatabase

# --- Input Models ---

class StoreItemInput(BaseModel):
    item_name: str = Field(description="Name of the item to store")
    place_name: str = Field(description="Where the item is being stored")

class RetrieveItemInput(BaseModel):
    item_name: str = Field(description="Name of the item to find")

class ListItemsInput(BaseModel):
    query: str = Field(default="all", description="Query filter for items")
    visual: bool = Field(default=False, description="Whether to show items in the interactive viewer")

# --- Tool Functions ---

def get_visitor_log(query: str) -> str:
    """Reads the visitor log file."""
    logger.info(f"Tool called: get_visitor_log with query='{query}'")
    try:
        if not Config.VISITOR_LOG_PATH.exists():
            return "No visitor log found."
        
        with open(Config.VISITOR_LOG_PATH, "r") as f:
            logs = f.read()
        return logs if logs else "The visitor log is empty."
    except Exception as e:
        logger.error(f"Error reading visitor log: {e}")
        return f"Error reading visitor log: {e}"

def answer_general_question(query: str) -> str:
    """Placeholder for general questions."""
    logger.info(f"Tool called: answer_general_question with query='{query}'")
    return f"I heard your question: '{query}', but I can only answer visitor log related queries for now."

def store_item_location_structured(
    item_name: str, 
    place_name: str, 
    frame_request_queue: Queue, 
    frame_response_queue: Queue,
    db: ItemDatabase
) -> str:
    """Stores item location with an image capture."""
    logger.info(f"Tool called: store_item_location for item='{item_name}' at place='{place_name}'")
    
    # Request frame
    frame_request_queue.put("CAPTURE")
    try:
        frame = frame_response_queue.get(timeout=3)
    except Exception:
        return "Failed to capture image for item storage."

    # Save image
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filename = f"{item_name}_{timestamp_str}.jpg"
    image_path = Config.ITEM_FRAMES_DIR / image_filename
    
    try:
        cv2.imwrite(str(image_path), frame)
    except Exception as e:
        logger.error(f"Failed to save item image: {e}")
        return "Failed to save item image."

    # Log to DB
    success = db.log_item(item_name, place_name, str(image_path))
    
    if success:
        return f"Stored '{item_name}' in '{place_name}' with image captured at {timestamp_str}."
    else:
        return f"Failed to log '{item_name}' to database."

import subprocess
import sys
from notifier import notify

def _launch_viewer(results: list, item_name: str) -> str:
    """Helper to launch viewer for a list of database results."""
    count = len(results)
    if count == 0:
        return f"No items found for '{item_name}'."

    # Extract IDs for viewer
    item_ids = [str(r[0]) for r in results]
    
    # Speak immediately before blocking
    if item_name == "all items":
        msg = f"I found {count} items in total. Opening the viewer for you."
    elif count == 1:
        msg = f"I found one {item_name}. Opening the viewer for you."
    else:
        msg = f"I found {count} items matching {item_name}. Opening the viewer."
    notify(msg)
    
    try:
        viewer_script = Config.ROOT_DIR / "view_items.py"
        logger.info(f"Launching viewer for IDs: {item_ids}")
        
        result = subprocess.run(
            [sys.executable, str(viewer_script), "--ids"] + item_ids,
            check=False,
            capture_output=True,
            text=True
        )
        
        output = result.stdout
        deleted_count = 0
        if "Deleted" in output:
            import re
            match = re.search(r"Deleted (\d+) items", output)
            if match:
                deleted_count = int(match.group(1))
        
        logger.info(f"Viewer closed. User deleted {deleted_count} items.")
        
    except Exception as e:
        logger.error(f"Failed to launch viewer: {e}")
        return f"Found {count} items, but failed to open viewer: {e}"
        
    items_summary = ", ".join([f"'{r[1]}' at '{r[2]}'" for r in results])
    
    if deleted_count > 0:
        return f"User finished using the interactive viewer. They viewed {count} items: {items_summary}. IMPORTANT: They deleted {deleted_count} items. Briefly acknowledge the deletions. DO NOT list the remaining items again."
    else:
        return f"User finished using the interactive viewer. They viewed {count} items: {items_summary}. They did not delete anything. Just say a brief friendly wrap-up (e.g. 'Hope that helped!'). DO NOT list the items again."

def retrieve_item_location(item_name: str, db: ItemDatabase) -> str:
    """Finds item location via smart search and launches viewer."""
    logger.info(f"Tool called: retrieve_item_location for item='{item_name}'")
    results = db.search_items(item_name)
    if not results:
        return f"No items found for '{item_name}' (checked exact match, keywords, and recent items)."
    return _launch_viewer(results, item_name)

def list_all_items(query: str = "all", db: ItemDatabase = None, visual: bool = True) -> str:
    """Lists stored items. Launches the interactive viewer by default."""
    logger.info(f"Tool called: list_all_items with query='{query}', visual={visual}")
    
    # If query is a generic "all" or similar, search for everything
    search_q = "" if query.lower() in ["all", "everything", "current", "items"] else query
    items = db.search_items(search_q) 
    
    if not items:
        if search_q:
            return f"No items found matching '{search_q}'."
        return "There are no items currently stored in the database."
    
    # Always launch viewer for this tool as per user request
    return _launch_viewer(items, query if search_q else "all items")

# --- Factory ---

def get_tools(frame_request_queue: Queue, frame_response_queue: Queue) -> list:
    """
    Returns the list of tools for the agent.
    Injects dependencies (queues, db) into the functions.
    """
    # Initialize DB (singleton-ish for this session)
    db = ItemDatabase(Config.DB_PATH)

    return [
        Tool(
            name="GetVisitorLog",
            func=get_visitor_log,
            description="Answer questions about who visited the room and when based on logs.",
        ),
        StructuredTool.from_function(
            func=partial(list_all_items, db=db),
            name="ListStoredItems",
            description="Use this when the user wants to see all stored items. It immediately opens the interactive viewer showing every item on record.",
            args_schema=ListItemsInput,
        ),
        StructuredTool.from_function(
            func=partial(
                store_item_location_structured,
                frame_request_queue=frame_request_queue,
                frame_response_queue=frame_response_queue,
                db=db
            ),
            name="StoreItemLocation",
            description="Use this when the user wants to store or save the location of an item. Extract item_name and place_name.",
            args_schema=StoreItemInput,
        ),
        StructuredTool.from_function(
            func=partial(retrieve_item_location, db=db),
            name="RetrieveItemLocation",
            description="Use this when the user asks for a SPECIFIC item (e.g., 'where is my pen'). It opens the viewer only for those matches.",
            args_schema=RetrieveItemInput,
        ),
    ]
