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

def main():
    print("SYSTEM: Supervisor initialized. Monitoring agent process...")
    
    # Initialize virtual environment if it doesn't exist
    if not os.path.exists(VENV_DIR):
        print("SYSTEM: Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
    
    # Install dependencies on boot
    if os.path.exists("requirements.txt"):
        print("SYSTEM: Installing dependencies from requirements.txt...")
        subprocess.run([VENV_PYTHON, "-m", "pip", "install", "-r", "requirements.txt"])

    # Ensure a barebones loop.py exists on the very first run if you haven't written one
    if not os.path.exists(AGENT_SCRIPT):
        with open(AGENT_SCRIPT, "w") as f:
            f.write("print('Hello World. I am alive.')\n")
            
    # Create initial backup if it doesn't exist
    if not os.path.exists(BACKUP_SCRIPT) and os.path.exists(AGENT_SCRIPT):
        shutil.copy2(AGENT_SCRIPT, BACKUP_SCRIPT)

    while True:
        print(f"\n--- SYSTEM: Booting {AGENT_SCRIPT} ---")
        
        # Open a file to capture any stderr output (like Python tracebacks)
        with open(CRASH_LOG, "w") as error_file:
            
            # We run the agent's code inside the virtual environment
            # -u forces unbuffered output so print() statements show up instantly in Docker logs.
            process = subprocess.Popen(
                [VENV_PYTHON, "-u", AGENT_SCRIPT], 
                stdout=sys.stdout,  # Stream normal thoughts/prints directly to console
                stderr=error_file   # Route errors to the log file
            )
            
            # Wait for the agent's loop to finish or crash
            process.wait()
        
        # Check how the agent exited
        if process.returncode != 0:
            print(f"\nSYSTEM: Agent crashed with exit code {process.returncode}.")
            
            # Read the crash log and print it to the Docker console for your visibility
            with open(CRASH_LOG, "r") as f:
                error_content = f.read()
                print(f"SYSTEM: Crash Traceback:\n{error_content}")
            
            print("SYSTEM: The traceback is saved to 'crash_report.txt'.")
            
            # Rollback logic
            if os.path.exists(BACKUP_SCRIPT):
                print(f"SYSTEM: Rolling back {AGENT_SCRIPT} to last known good state...")
                shutil.copy2(BACKUP_SCRIPT, AGENT_SCRIPT)
            
            print("SYSTEM: Rebooting in 10 seconds to prevent rapid crash loops...")
            time.sleep(10)
            
        else:
            print("\nSYSTEM: Agent exited cleanly (Code 0).")
            print("SYSTEM: Backing up stable state...")
            if os.path.exists(AGENT_SCRIPT):
                shutil.copy2(AGENT_SCRIPT, BACKUP_SCRIPT)
                
            # Check for new dependencies before rebooting
            if os.path.exists("requirements.txt"):
                print("SYSTEM: Checking for new dependencies...")
                subprocess.run([VENV_PYTHON, "-m", "pip", "install", "-r", "requirements.txt"])
                
            print("SYSTEM: Rebooting in 2 seconds to apply any self-modifications...")
            time.sleep(2)

if __name__ == "__main__":
    main()
