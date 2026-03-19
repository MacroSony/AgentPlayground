import os
import json
import time

SCHEDULE_FILE = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "schedule.json")

def _load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, "r") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return data
        except Exception:
            return []
    return []

def _save_schedule(schedule):
    temp_file = SCHEDULE_FILE + ".tmp"
    try:
        with open(temp_file, "w") as f:
            json.dump(schedule, f, indent=2)
        os.replace(temp_file, SCHEDULE_FILE)
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def add_scheduled_task(description: str, interval_seconds: int = None, run_at: float = None) -> str:
    """Adds a scheduled task that will trigger a message to the agent's inbox.
    
    Args:
        description: The task description/prompt to send when triggered.
        interval_seconds: If provided, the task will repeat every X seconds.
        run_at: If provided, a Unix timestamp for a one-off task.
    """
    try:
        schedule = _load_schedule()
        task_id = 1 if not schedule else max(t.get("id", 0) for t in schedule) + 1
        
        new_task = {
            "id": task_id,
            "description": description,
            "last_run": time.time() if interval_seconds else None,
        }
        
        if interval_seconds is not None:
            new_task["interval_seconds"] = int(interval_seconds)
        elif run_at is not None:
            new_task["run_at"] = float(run_at)
        else:
            return "Error: Must provide either interval_seconds or run_at."
            
        schedule.append(new_task)
        _save_schedule(schedule)
        return f"Scheduled task added with ID: {task_id}"
    except Exception as e:
        return f"Error adding scheduled task: {e}"

def list_scheduled_tasks() -> str:
    """Lists all scheduled tasks."""
    try:
        schedule = _load_schedule()
        if not schedule:
            return "No scheduled tasks found."
            
        output = ["Scheduled Tasks:"]
        for t in schedule:
            details = f"Interval: {t.get('interval_seconds')}s" if "interval_seconds" in t else f"Run At: {t.get('run_at')}"
            output.append(f"[{t['id']}] {t['description']} ({details})")
        return "\n".join(output)
    except Exception as e:
        return f"Error listing scheduled tasks: {e}"

def remove_scheduled_task(task_id: int) -> str:
    """Removes a scheduled task by ID."""
    try:
        schedule = _load_schedule()
        new_schedule = [t for t in schedule if t["id"] != task_id]
        if len(schedule) == len(new_schedule):
            return f"Scheduled task {task_id} not found."
            
        _save_schedule(new_schedule)
        return f"Scheduled task {task_id} removed."
    except Exception as e:
        return f"Error removing scheduled task: {e}"

def check_and_trigger_scheduled_tasks():
    """Checks scheduled tasks and adds triggered ones to the inbox."""
    try:
        schedule = _load_schedule()
        if not schedule:
            return
            
        current_time = time.time()
        triggered_tasks = []
        updated_schedule = []
        
        for t in schedule:
            triggered = False
            if "interval_seconds" in t:
                if current_time - t.get("last_run", 0) >= t["interval_seconds"]:
                    triggered = True
                    t["last_run"] = current_time
                updated_schedule.append(t)
            elif "run_at" in t:
                if current_time >= t["run_at"]:
                    triggered = True
                else:
                    updated_schedule.append(t)
                    
            if triggered:
                triggered_tasks.append(t["description"])
                
        if triggered_tasks:
            _save_schedule(updated_schedule)
            inbox_path = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "inbox.txt")
            with open(inbox_path, "a") as f:
                for desc in triggered_tasks:
                    f.write(f"[SCHEDULED TASK TRIGGERED] {desc}\n")
    except Exception as e:
        print(f"AGENT: Error checking scheduled tasks: {e}")
