
from database import ItemDatabase
from config import Config
import os

def test_search():
    db = ItemDatabase(Config.DB_PATH)
    
    print("Logging test items...")
    # Use dummy paths
    db.log_item("Test Red Apple", "Table", "dummy_path.jpg")
    db.log_item("Test Green Apple", "Fridge", "dummy_path.jpg")
    db.log_item("Test Keys", "Door", "dummy_path.jpg")
    
    print("\n--- Testing Exact Search 'Test Keys' ---")
    res = db.search_items("Test Keys")
    print(f"Found: {[r[1] for r in res]}")
    assert any("test keys" in r[1] for r in res)
    
    print("\n--- Testing Token Search 'Apple' ---")
    res = db.search_items("Apple")
    print(f"Found: {[r[1] for r in res]}")
    # Should find Red and Green
    assert len([r for r in res if "apple" in r[1]]) >= 2
    
    print("\n--- Testing Recent Search (Fallback) for 'NonExistentItem' ---")
    res = db.search_items("NonExistentItem")
    print(f"Found (Recent): {[r[1] for r in res]}")
    assert len(res) > 0
    
    print("\n--- Testing Deletion & File Cleanup ---")
    # Find one item to delete
    res = db.search_items("Test Red Apple")
    if res:
        item_id = res[0][0]
        image_path = res[0][4]
        
        # Create dummy file if not exists
        with open(image_path, 'w') as f:
            f.write("dummy")
            
        print(f"Deleting ID {item_id} ({res[0][1]})")
        db.delete_item(item_id)
        
        # Verify it's gone from DB
        res_after = db.search_items("Test Red Apple")
        # Check if specific ID is gone
        assert item_id not in [r[0] for r in res_after]
        
        # Verify file is gone
        if os.path.exists(image_path):
            print(f"❌ File {image_path} was NOT deleted.")
            raise AssertionError("File cleanup failed")
        else:
            print(f"✅ File {image_path} was confirmed deleted.")
            
        print("Deletion verified.")
    
    print("\n✅ Verification passed.")

if __name__ == "__main__":
    test_search()
