import os
import json

TASKS_FILE = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "tasks.json")

def _load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

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
    """Updates the status of a specific task.

    Args:
        task_id: The unique ID of the task.
        status: The new status (e.g., 'todo', 'in_progress', 'done', 'blocked').
    """
    try:
        tasks = _load_tasks()
        for t in tasks:
            if t["id"] == task_id:
                t["status"] = status
                _save_tasks(tasks)
                return f"Task {task_id} status updated to '{status}'."
        return f"Task with ID {task_id} not found."
    except Exception as e:
        return f"Error updating task: {e}"
