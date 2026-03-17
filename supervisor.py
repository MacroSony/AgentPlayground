import subprocess
import time
import sys
import os
import shutil

AGENT_SCRIPT = "loop.py"
BACKUP_SCRIPT = ".backup_loop.py"
CRASH_LOG = "crash_report.txt"
VENV_DIR = ".venv"
VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python")

def _setup_environment():
    """Initializes the virtual environment and installs dependencies."""
    if not os.path.exists(VENV_DIR):
        print("SYSTEM: Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
    
    if os.path.exists("requirements.txt"):
        print("SYSTEM: Installing dependencies from requirements.txt...")
        subprocess.run([VENV_PYTHON, "-m", "pip", "install", "-r", "requirements.txt"])

def _ensure_agent_files():
    """Ensures agent script and its backup exist."""
    if not os.path.exists(AGENT_SCRIPT):
        with open(AGENT_SCRIPT, "w") as f:
            f.write("print('Hello World. I am alive.')\n")
            
    if not os.path.exists(BACKUP_SCRIPT) and os.path.exists(AGENT_SCRIPT):
        shutil.copy2(AGENT_SCRIPT, BACKUP_SCRIPT)

def _run_agent():
    """Runs the agent process and handles its exit."""
    print(f"\n--- SYSTEM: Booting {AGENT_SCRIPT} ---")
    with open(CRASH_LOG, "w") as error_file:
        process = subprocess.Popen(
            [VENV_PYTHON, "-u", AGENT_SCRIPT], 
            stdout=sys.stdout,
            stderr=error_file
        )
        process.wait()
    return process.returncode

def _handle_crash(returncode):
    """Handles agent crash by logging and rolling back."""
    print(f"\nSYSTEM: Agent crashed with exit code {returncode}.")
    with open(CRASH_LOG, "r") as f:
        print(f"SYSTEM: Crash Traceback:\n{f.read()}")
    
    if os.path.exists(BACKUP_SCRIPT):
        print(f"SYSTEM: Rolling back {AGENT_SCRIPT} to last known good state...")
        shutil.copy2(BACKUP_SCRIPT, AGENT_SCRIPT)
    
    print("SYSTEM: Rebooting in 10 seconds...")
    time.sleep(10)

def _handle_clean_exit():
    """Handles clean exit by backing up and checking dependencies."""
    print("\nSYSTEM: Agent exited cleanly (Code 0).")
    print("SYSTEM: Backing up stable state...")
    if os.path.exists(AGENT_SCRIPT):
        shutil.copy2(AGENT_SCRIPT, BACKUP_SCRIPT)
        
    if os.path.exists("requirements.txt"):
        print("SYSTEM: Checking for new dependencies...")
        subprocess.run([VENV_PYTHON, "-m", "pip", "install", "-r", "requirements.txt"])
        
    print("SYSTEM: Rebooting in 2 seconds...")
    time.sleep(2)

def main():
    print("SYSTEM: Supervisor initialized. Monitoring agent process...")
    _setup_environment()
    _ensure_agent_files()

    while True:
        returncode = _run_agent()
        if returncode != 0:
            _handle_crash(returncode)
        else:
            _handle_clean_exit()

if __name__ == "__main__":
    main()
