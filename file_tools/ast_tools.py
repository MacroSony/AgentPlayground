import ast
import os

def analyze_python_file(filepath: str) -> str:
    """Analyzes a Python file and returns a summary of its classes and functions.
    
    Args:
        filepath: The path to the file relative to /app/agent.
    """
    AGENT_ROOT = os.path.realpath(os.getenv("AGENT_ROOT", os.getcwd()))
    safe_path = os.path.realpath(os.path.join(AGENT_ROOT, filepath))
    if not (safe_path == AGENT_ROOT or safe_path.startswith(f"{AGENT_ROOT}{os.sep}")):
        return f"Error: Path is outside allowed root: {filepath}"
    
    if not os.path.exists(safe_path):
        return f"Error: File {filepath} not found."
    
    try:
        with open(safe_path, 'r') as f:
            tree = ast.parse(f.read())
            
        # Better approach: top-level only or structured
        structured_summary = [f"Structure of {filepath}:"]
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                structured_summary.append(f"\nClass: {node.name}")
                doc = ast.get_docstring(node)
                if doc:
                    structured_summary.append(f"  Doc: {doc.splitlines()[0]}...")
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        structured_summary.append(f"  Method: {item.name}")
            elif isinstance(node, ast.FunctionDef):
                structured_summary.append(f"\nFunction: {node.name}")
                doc = ast.get_docstring(node)
                if doc:
                    structured_summary.append(f"  Doc: {doc.splitlines()[0]}...")
                    
        return "\n".join(structured_summary)
    except Exception as e:
        return f"Error analyzing file {filepath}: {e}"

def summarize_project() -> str:
    """Provides a structural summary of all Python files in the project."""
    AGENT_ROOT = os.path.realpath(os.getenv("AGENT_ROOT", os.getcwd()))
    project_summary = ["Project Structure:"]
    
    for root, _, files in os.walk(AGENT_ROOT):
        # Exclude hidden and environment directories
        if ".venv" in root or ".git" in root or "__pycache__" in root or ".cache" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, AGENT_ROOT)
                res = analyze_python_file(rel_path)
                project_summary.append(f"\n--- {rel_path} ---")
                project_summary.append("\n".join("  " + line for line in res.splitlines()))
                
    return "\n".join(project_summary)
