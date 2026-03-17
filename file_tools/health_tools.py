import os
import psutil
import time
import json
import ast

def _scan_file_health(filepath, rel_path, results, markers):
    """Scans a single file for health issues."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            content = "".join(lines)
            
            # 1. Markers (TO-DO/FIX-ME)
            for i, line in enumerate(lines, 1):
                for m in markers:
                    if m in line:
                        results["markers"].append(f"{rel_path}:{i}: {line.strip()}")
            
            # 2. Large Functions & Bare Excepts
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        start_line = node.lineno
                        end_line = getattr(node, 'end_lineno', start_line)
                        length = end_line - start_line
                        if length > 50:
                            results["large_functions"].append(f"{rel_path}:{start_line}: Function '{node.name}' is long ({length} lines).")
                    
                    if isinstance(node, ast.ExceptHandler):
                        if node.type is None:
                            results["issues"].append(f"{rel_path}:{node.lineno}: Bare except block found.")
            except SyntaxError as e:
                results["issues"].append(f"Error processing {rel_path}: {e}")
            except Exception as e:
                results["issues"].append(f"Error processing {rel_path}: {e}")
            
            # 3. Unsafe Practices
            if "ex" + "ec(" in content:
                results["unsafe"].append(f"{rel_path}: Use of 'exec' detected.")
            if "ev" + "al(" in content:
                results["unsafe"].append(f"{rel_path}: Use of 'eval' detected.")
    except Exception as e:
        results["issues"].append(f"Error opening {rel_path}: {e}")

def check_code_health(directory: str) -> str:
    """Scans the codebase for TO-DOs, FIX-MEs, and potential code quality issues."""
    from file_tools.tools import resolve_safe_path
    try:
        safe_dir = resolve_safe_path(directory)
        results = {"markers": [], "large_functions": [], "unsafe": [], "issues": []}
        markers = ["TO" + "DO", "FIX" + "ME", "B" + "UG", "HA" + "CK"]
        
        for root, _, files in os.walk(safe_dir):
            if any(p in root for p in [".git", ".venv", "__pycache__", ".cache"]): continue
            for file in files:
                if not file.endswith(".py"): continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, safe_dir)
                _scan_file_health(filepath, rel_path, results, markers)
        
        output = []
        if results["markers"]:
            output.append("#### Markers (TO" + "DO/FIX" + "ME/etc) ####")
            output.extend(results["markers"])
        if results["large_functions"]:
            output.append("#### Complexity: Large Functions (>50 lines) ####")
            output.extend(results["large_functions"])
        if results["unsafe"]:
            output.append("#### Safety Warnings ####")
            output.extend(results["unsafe"])
        if results["issues"]:
            output.append("#### Issues / Errors ####")
            output.extend(results["issues"])
            
        return "\n".join(output) if output else "No issues or markers found. Code looks healthy!"
    except Exception as e: return f"Error checking code health: {e}"

RESOURCE_LOG = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "resource_usage.json")

def get_current_resources() -> dict:
    """Fetches current CPU and Memory usage of the agent process."""
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return {
            "timestamp": time.time(),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_rss": mem_info.rss,
            "memory_vms": mem_info.vms,
            "num_threads": process.num_threads(),
            "uptime": time.time() - psutil.boot_time()
        }
    except Exception as e: return {"error": str(e)}

def log_resource_usage() -> str:
    """Logs the current resource usage to a persistent JSON file."""
    try:
        data = get_current_resources()
        if "error" in data: return f"Error getting resources: {data['error']}"
        history = []
        if os.path.exists(RESOURCE_LOG):
            with open(RESOURCE_LOG, "r") as f: history = json.load(f)
        history.append(data)
        history = history[-100:]
        with open(RESOURCE_LOG, "w") as f: json.dump(history, f, indent=2)
        return f"Resource usage logged at {time.ctime(data['timestamp'])}"
    except Exception as e: return f"Error logging resources: {e}"

def get_resource_summary() -> str:
    """Returns a formatted summary of recent resource usage."""
    try:
        if not os.path.exists(RESOURCE_LOG): return "No resource history found."
        with open(RESOURCE_LOG, "r") as f: history = json.load(f)
        if not history: return "Resource history is empty."
        latest = history[-1]
        summary = [f"### Resource Usage Summary ({time.ctime(latest['timestamp'])}) ###"]
        summary.append(f"- CPU: {latest['cpu_percent']}%")
        summary.append(f"- Memory (RSS): {latest['memory_rss'] / (1024*1024):.2f} MB")
        summary.append(f"- Threads: {latest['num_threads']}")
        summary.append(f"- Uptime: {latest['uptime'] / 3600:.2f} hours")
        if len(history) > 1:
            avg_cpu = sum(h['cpu_percent'] for h in history) / len(history)
            avg_mem = sum(h['memory_rss'] for h in history) / (len(history) * 1024 * 1024)
            summary.append(f"\nAverage (last {len(history)} samples):")
            summary.append(f"- Avg CPU: {avg_cpu:.2f}%")
            summary.append(f"- Avg Memory: {avg_mem:.2f} MB")
        return "\n".join(summary)
    except Exception as e: return f"Error getting resource summary: {e}"
