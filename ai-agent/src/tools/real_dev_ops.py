
import subprocess
import os
import sys

class RealDevOps:
    @staticmethod
    def update_file(file_path: str, search_str: str, replace_str: str, commit_message: str):
        print(f"🔧 [DevOps] Modifying {file_path}...")
        
        # Read
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return {"status": "FAILED", "error": f"File not found: {file_path}"}

        # Replace
        if search_str not in content:
             return {"status": "FAILED", "error": f"Search string not found in {file_path}"}
        
        new_content = content.replace(search_str, replace_str)
        
        # Write
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        # Git Cycle
        try:
            print("  -> Git Add...")
            subprocess.run(["git", "add", file_path], check=True, capture_output=True)
            print("  -> Git Commit...")
            subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True)
            print("  -> Git Push...")
            # Using specific branch logic if needed, usually just 'git push' works if upstream set
            subprocess.run(["git", "push", "origin", "master"], check=True, capture_output=True)
            print("✅ [DevOps] Push Successful!")
            return {"status": "SUCCESS", "details": f"Deployed: {commit_message}"}
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode() if e.stderr else str(e)
            print(f"❌ [DevOps] Git Error: {err_msg}")
            return {"status": "FAILED", "error": err_msg}

if __name__ == "__main__":
    # Direct execution for CEO command
    # Path is relative to where script is run. Assuming root of workspace.
    
    TARGET_FILE = "hostamar-platform/app/page.tsx"
    OLD_TEXT = "আপনার ব্যবসা সেটআপ করুন + প্রতিদিন পান মার্কেটিং ভিডিও"
    NEW_TEXT = "AI-Powered Cloud Hosting & Automated Marketing"
    COMMIT_MSG = "Feat(Content): Update Hero Headline for Global Launch"

    RealDevOps.update_file(TARGET_FILE, OLD_TEXT, NEW_TEXT, COMMIT_MSG)
