import os
import time
from file_tools.tools import get_usage, load_memory
from file_tools.tasks import list_tasks
from file_tools.git_tools import git_status
from file_tools.health_tools import check_code_health, get_resource_summary
import subprocess

def run_test_suite() -> str:
    """Runs the full test suite and returns the output summary."""
    try:
        result = subprocess.run(["./run_tests.sh"], capture_output=True, text=True, timeout=60)
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        
        # Extract just the summary line
        lines = output.strip().split('\n')
        summary = "No summary found."
        for line in reversed(lines):
            if "Ran " in line and " tests in " in line:
                summary = line
                break
        
        status = "PASSED" if result.returncode == 0 else "FAILED"
        return f"Test Suite: {status}\n{summary}"
    except Exception as e:
        return f"Error running tests: {e}"

def _build_status_report() -> list:
    report = [f"# Hoshi Status Report - {time.strftime('%Y-%m-%d %H:%M:%S')}"]
    report.append("\n## API Usage")
    report.append(get_usage())
    report.append("\n## Tasks")
    report.append(list_tasks())
    return report

def _append_inbox_status(report: list):
    report.append("\n## Inbox (Latest Messages)")
    try:
        inbox_processing = "inbox_processing.txt"
        if os.path.exists(inbox_processing):
            with open(inbox_processing, "r") as f:
                messages = f.readlines()[-5:]
                if messages:
                    report.extend([f"- {m.strip()}" for m in messages])
                else:
                    report.append("Inbox is empty.")
        else:
            report.append("Inbox processing file not found.")
    except Exception as e:
        report.append(f"Error reading inbox: {e}")

def _append_health_status(report: list):
    report.append("\n## Git Status")
    report.append(git_status())
    report.append("\n## Code Health & Tests")
    report.append(run_test_suite())
    report.append("\n" + get_resource_summary())
    health = check_code_health(".")
    health_lines = health.split('\n')
    report.append('\n'.join(health_lines[:15]))
    if len(health_lines) > 15:
        report.append("... (see full health report for details)")

def _append_recent_activity(report: list):
    report.append("\n## Recent Activity (from Memory)")
    memory = load_memory()
    entries = memory.get("entries", [])
    status_entries = [e for e in entries if "status" in e.get("metadata", {}).get("tags", [])]
    for entry in status_entries[-3:]:
        ts = entry.get("metadata", {}).get("timestamp", "unknown")
        text = entry.get("text", "")
        summary = text[:200] + "..." if len(text) > 200 else text
        report.append(f"- [{ts}] {summary}")

def generate_status_report() -> str:
    """Generates a comprehensive status report of the agent's current state."""
    try:
        report = _build_status_report()
        _append_inbox_status(report)
        _append_health_status(report)
        _append_recent_activity(report)
        return "\n".join(report)
    except Exception as e:
        return f"Error generating status report: {e}"
