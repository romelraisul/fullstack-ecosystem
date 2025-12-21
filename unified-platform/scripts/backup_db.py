import shutil
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def backup_db():
    db_url = os.getenv("DATABASE_URL", "sqlite:///./data/unified_platform.db")
    if not db_url.startswith("sqlite:///"):
        print("Only SQLite backups are supported by this script.")
        return
    
    db_path = db_url.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"unified_platform_{timestamp}.db")
    
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backed up to {backup_path}")

if __name__ == "__main__":
    backup_db()
