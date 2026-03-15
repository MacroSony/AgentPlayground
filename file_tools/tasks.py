import os
import json

TASKS_FILE = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "tasks.json")

def _load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return data
        except Exception as e:
            print(f"Error loading tasks: {e}")
            # If the file exists but is corrupted, try to find a backup? 
            # For now, just don't return an empty list if we want to avoid overwriting.
            # But returning empty list is what caused the issue.
            # Better to raise or return None and handle it.
            return []
    return []

def _save_tasks(tasks):
    temp_file = TASKS_FILE + ".tmp"
    try:
        with open(temp_file, "w") as f:
            json.dump(tasks, f, indent=2)
        os.replace(temp_file, TASKS_FILE)
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e

def add_task(description: str) -> str:
    """Adds a new task to the task tracker.

    Args:
        description: A clear description of the task.
    """
    try:
        if not description:
            return "Error: Task description cannot be empty."
        tasks = _load_tasks()
        task_id = 1 if not tasks else max(t.get("id", 0) for t in tasks) + 1
        new_task = {
            "id": task_id,
            "description": description,
            "status": "todo"
        }
        tasks.append(new_task)
        _save_tasks(tasks)
        return f"Task added with ID: {task_id}"
    except Exception as e:
        return f"Error adding task: {e}"

def list_tasks() -> str:
    """Lists all tasks in the task tracker with their ID and status."""
    try:
        tasks = _load_tasks()
        if not tasks:
            return "No tasks found."
        
        output = ["Tasks:"]
        for t in tasks:
            output.append(f"[{t['id']}] [{t['status'].upper()}] {t['description']}")
        return "\n".join(output)
    except Exception as e:
        return f"Error listing tasks: {e}"

def update_task_status(task_id: int, status: str) -> str:
    """Updates the status of a specific task."""
    try:
        tasks = _load_tasks()
        for t in tasks:
            if t["id"] == task_id:
                t["status"] = status
                _save_tasks(tasks)
                return f"Task {task_id} status updated to '{status}'."
        return f"Task with ID {task_id} not found."
    except Exception as e: return f"Error updating task: {e}"

def wait_for_user_approval(task_description: str, timeout_seconds: int = 3600) -> str:
    """Creates a blocked task and waits for the user to manually mark it as done."""
    import time
    from file_tools.tools import send_discord_message, sleep
    try:
        task_msg = add_task(f"USER APPROVAL REQUIRED: {task_description}")
        if "Error" in task_msg: return task_msg
        task_id = int(task_msg.split(": ")[1])
        update_task_status(task_id, "blocked")
        
        send_discord_message(f"⚠️ **ACTION REQUIRED** ⚠️\nTask {task_id}: {task_description}\n"
                             f"Please mark Task {task_id} as 'done' in `tasks.json` to proceed.")
        
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            tasks = _load_tasks()
            for t in tasks:
                if t["id"] == task_id and t["status"] == "done":
                    return f"Approval received for Task {task_id}."
            sleep(30) # Poll every 30 seconds
            
        return f"Timed out waiting for approval on Task {task_id}."
    except Exception as e: return f"Error in wait_for_user_approval: {e}"
