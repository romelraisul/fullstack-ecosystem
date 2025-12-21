import subprocess
import time
import sys
import os
import signal
from datetime import datetime

def run_service():
    backend_path = os.path.join(os.path.dirname(__file__), "../src/advanced_backend.py")
    log_dir = os.path.join(os.path.dirname(__file__), "../logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file_path = os.path.join(log_dir, f"backend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    print(f"🚀 Launching Unified Platform Backend...")
    print(f"📋 Logs: {log_file_path}")
    
    with open(log_file_path, "a") as log_file:
        while True:
            try:
                process = subprocess.Popen(
                    [sys.executable, backend_path],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                print(f"✅ Backend started (PID: {process.pid})")
                
                # Wait for process to finish
                exit_code = process.wait()
                
                if exit_code != 0:
                    print(f"⚠️ Backend crashed with exit code {exit_code}. Restarting in 5s...")
                    time.sleep(5)
                else:
                    print(f"ℹ️ Backend stopped gracefully. Exiting launcher.")
                    break
                    
            except KeyboardInterrupt:
                print("\n🛑 Launcher stopping...")
                process.terminate()
                break
            except Exception as e:
                print(f"❌ Launcher error: {e}. Restarting in 10s...")
                time.sleep(10)

if __name__ == "__main__":
    run_service()
