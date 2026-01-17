
import cv2
import argparse
import numpy as np
import time
from pathlib import Path
from database import ItemDatabase
from config import Config

def create_info_image(text: str, bg_color=(0, 0, 0)):
    """Creates a standalone image with text."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = bg_color
    
    # Split text into lines
    y = 200
    for line in text.split('\n'):
        cv2.putText(img, line, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        y += 40

    controls = "Press 'q' to close"
    cv2.putText(img, controls, (50, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    return img

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="+", type=int, help="List of Item IDs to view")
    args = parser.parse_args()

    if not args.ids:
        print("No IDs provided.")
        return

    db = ItemDatabase(Config.DB_PATH)
    items_to_view = args.ids
    
    deleted_count = 0
    i = 0
    
    print(f"Starting viewer for IDs: {items_to_view}")

    # Create window
    window_name = "Item Viewer - Video Agent"
    cv2.namedWindow(window_name)
    cv2.moveWindow(window_name, 100, 100) # Attempt to position on screen

    while i < len(items_to_view):
        item_id = items_to_view[i]
        
        # Fetch current details (in case it was deleted externally, or to verify)
        try:
            # We need to fetch details. The DB class doesn't have "get_by_id".
            # Let's just do a quick manual query or rely on "search" logic?
            # Or add get_by_id to DB? 
            # For now, let's just assume we need to execute a query.
            # But wait, `view_items.py` imports `ItemDatabase`.
            # I can add a helper or just run raw SQL here since it's a helper script.
            # Actually, reusing `find_item` is hard if we only have ID.
            # Let's stick to the DB connection for simplicity.
            
            import sqlite3
            with sqlite3.connect(Config.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT item_name, place_name, timestamp, image_path FROM item_log WHERE id = ?", (item_id,))
                result = cursor.fetchone()
            
            if not result:
                # Item might have been deleted
                i += 1
                continue

            name, place, timestamp, image_path = result
            
            # Load Image
            img = cv2.imread(image_path)
            if img is None:
                img = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(img, "Image File Missing", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Overlay Text
            # Top Banner
            cv2.rectangle(img, (0, 0), (640, 60), (0, 0, 0), -1)
            cv2.putText(img, f"ID: {item_id} | {name.upper()}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(img, f"At: {place}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            # Bottom Controls
            cv2.rectangle(img, (0, 420), (640, 480), (0, 0, 0), -1)
            controls = "[n]ext | [d]elete | [q]uit"
            cv2.putText(img, controls, (20, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow(window_name, img)
            
            # Wait for key
            key = cv2.waitKey(0) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('n'):
                i += 1
            elif key == ord('d'):
                # Delete
                if db.delete_item(item_id):
                    deleted_count += 1
                    # Visual Feedback
                    overlay = img.copy()
                    cv2.rectangle(overlay, (150, 200), (490, 280), (0, 0, 255), -1)
                    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
                    cv2.putText(img, "DELETED", (180, 255), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
                    
                    cv2.imshow(window_name, img)
                    cv2.waitKey(800) # Show for 0.8s
                i += 1
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error viewing item {item_id}: {e}")
            i += 1

    cv2.destroyAllWindows()
    # cv2.waitKey(1)
    print(f"Deleted {deleted_count} items.")

if __name__ == "__main__":
    main()
