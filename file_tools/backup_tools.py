import os
import shutil
import time
import json

BACKUP_DIR = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), ".backups")
FILES_TO_BACKUP = [
    "long_term_memory.json",
    "tasks.json",
    "resource_usage.json",
    "active_model.txt",
    "dev_log.txt"
]

def backup_data(extra_files: list = None) -> str:
    """Creates a timestamped backup of key data files."""
    try:
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
        os.makedirs(backup_path)
        
        files_to_backup = FILES_TO_BACKUP.copy()
        if extra_files:
            files_to_backup.extend(extra_files)
        
        backed_up = []
        for filename in files_to_backup:
            src = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), filename)
            if os.path.exists(src):
                shutil.copy2(src, backup_path)
                backed_up.append(filename)
                
        # Create a metadata file
        with open(os.path.join(backup_path, "metadata.json"), "w") as f:
            json.dump({
                "timestamp": time.time(),
                "files": backed_up
            }, f, indent=2)
            
        return f"Successfully created backup in {backup_path}. Files: {', '.join(backed_up)}"
    except Exception as e:
        return f"Error during backup: {e}"

def list_backups() -> str:
    """Lists available backups."""
    try:
        if not os.path.exists(BACKUP_DIR):
            return "No backups found."
            
        backups = sorted(os.listdir(BACKUP_DIR), reverse=True)
        if not backups:
            return "No backups found."
            
        output = ["Available Backups:"]
        for b in backups:
            meta_path = os.path.join(BACKUP_DIR, b, "metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                output.append(f"- {b} ({len(meta['files'])} files)")
            else:
                output.append(f"- {b} (no metadata)")
        return "\n".join(output)
    except Exception as e:
        return f"Error listing backups: {e}"

def restore_data(backup_name: str) -> str:
    """Restores data from a specific backup."""
    try:
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        if not os.path.exists(backup_path):
            return f"Error: Backup '{backup_name}' not found."
            
        files = os.listdir(backup_path)
        restored = []
        for filename in files:
            if filename == "metadata.json":
                continue
            src = os.path.join(backup_path, filename)
            dst = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), filename)
            shutil.copy2(src, dst)
            restored.append(filename)
            
        return f"Successfully restored {len(restored)} files from {backup_name}: {', '.join(restored)}"
    except Exception as e:
        return f"Error during restore: {e}"
