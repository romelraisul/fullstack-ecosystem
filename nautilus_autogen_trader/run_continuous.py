import time
import subprocess
import requests
import sys

DASHBOARD_URL = "http://localhost:8000/health"
CHECK_INTERVAL = 300 # 5 minutes

def restart_system():
    print("[WATCHDOG] System Unresponsive. Initiating Restart Sequence...")
    try:
        subprocess.run(["docker-compose", "down"], check=True)
        time.sleep(10)
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        print("[WATCHDOG] System Restarted Successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[WATCHDOG] FATAL: Failed to restart system. Error: {e}")
        sys.exit(1)

def watchdog_loop():
    print(f"[WATCHDOG] Monitoring system at {DASHBOARD_URL}")
    while True:
        try:
            response = requests.get(DASHBOARD_URL, timeout=10)
            if response.status_code == 200:
                print(f"[WATCHDOG] Health Check PASSED at {time.ctime()}")
            else:
                print(f"[WATCHDOG] Health Check FAILED. Status: {response.status_code}")
                restart_system()
        except requests.exceptions.RequestException as e:
            print(f"[WATCHDOG] Connection Error: {e}")
            restart_system()
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    watchdog_loop()
