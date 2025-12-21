"""
Hostamar AI Office Launcher (Single Window Version)
Launches all agents as background tasks to save system resources.
"""

import subprocess
import time
import sys
import os

def main():
    print("==========================================")
    print("   HOSTAMAR AI OFFICE: BOOT SEQUENCE      ")
    print("   (Optimized: Background Mode)           ")
    print("==========================================\n")

    base_path = "G:\\My Drive\\Automations\\ai-agent"
    
    agents = [
        ("Nova (CSO)", "chief_orchestrator.py"),
        ("Atlas (SRE)", "infrastructure_agent.py"),
        ("Silas (Sales)", "marketing_agent.py"),
        ("Lyra (QA)", "monitoring_agent.py")
    ]

    processes = []

    for name, script in agents:
        script_path = os.path.join(base_path, script)
        print(f"🚀 Starting {name}...")
        
        # Launch as background process, output redirected to logs
        log_file = open(os.path.join(base_path, "logs", f"{script}.log"), "a")
        proc = subprocess.Popen(
            [sys.executable, script_path],
            stdout=log_file,
            stderr=log_file,
            creationflags=subprocess.CREATE_NO_WINDOW # No more popups!
        )
        processes.append((name, proc))
        time.sleep(1)

    print("\n✅ Office is running in the background.")
    print(f"Check logs in {os.path.join(base_path, 'logs')}")
    
    # Optional: Keep script alive if you want to monitor here
    # For now, we exit and let the Watchdog monitor the PIDs.

if __name__ == "__main__":
    main()