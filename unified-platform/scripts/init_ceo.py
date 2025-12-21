import sys
import os
import requests
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

load_dotenv()

def init_ceo():
    email = "romelraisul@gmail.com"
    password = "MasterCEO_2025" # 15 chars, safe for bcrypt
    
    port = os.getenv("ADV_BACKEND_PORT", 8011)
    url = f"http://localhost:{port}/api/v1/auth/register"
    
    payload = {
        "username": email,
        "password": password
    }
    
    try:
        # We use requests assuming the backend might be running or we use repo directly
        # For safety, let's use the repository directly if backend isn't up
        from persistence import get_session, init_db
        from repository import UserRepository
        from auth_utils import get_password_hash
        
        init_db()
        session = get_session()
        repo = UserRepository(session)
        
        if repo.get_by_username(email):
            print(f"CEO Account {email} already exists.")
        else:
            hashed = get_password_hash(password)
            repo.create(email, hashed, role="admin")
            print(f"✅ CEO Account Created: {email}")
            print(f"🔑 Initial Password: {password}")
        
        session.close()
    except Exception as e:
        print(f"❌ Failed to init CEO: {e}")

if __name__ == "__main__":
    init_ceo()
