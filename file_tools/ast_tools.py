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
            
        structured_summary = [f"Structure of {filepath}:"]
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                structured_summary.append(f"\n[CLASS] {node.name}")
                doc = ast.get_docstring(node)
                if doc:
                    first_line = doc.splitlines()[0] if doc.strip() else ""
                    structured_summary.append(f"  Doc: {first_line}")
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        args = [arg.arg for arg in item.args.args if arg.arg != 'self']
                        structured_summary.append(f"  - [METHOD] {item.name}({', '.join(args)})")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = "[ASYNC FUNC]" if isinstance(node, ast.AsyncFunctionDef) else "[FUNC]"
                args = [arg.arg for arg in node.args.args]
                structured_summary.append(f"\n{kind} {node.name}({', '.join(args)})")
                doc = ast.get_docstring(node)
                if doc:
                    first_line = doc.splitlines()[0] if doc.strip() else ""
                    structured_summary.append(f"  Doc: {first_line}")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        structured_summary.append(f"[CONST/VAR] {target.id}")
                    
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

def find_definition(name: str) -> str:
    """Searches for the definition of a class or function across all Python files in the project.
    
    Args:
        name: The name of the class or function to find.
    """
    AGENT_ROOT = os.path.realpath(os.getenv("AGENT_ROOT", os.getcwd()))
    results = []
    
    for root, _, files in os.walk(AGENT_ROOT):
        if ".venv" in root or ".git" in root or "__pycache__" in root or ".cache" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        tree = ast.parse(f.read())
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.name == name:
                                rel_path = os.path.relpath(file_path, AGENT_ROOT)
                                lineno = node.lineno
                                kind = "Class" if isinstance(node, ast.ClassDef) else "Function"
                                results.append(f"{kind} '{name}' found in {rel_path} at line {lineno}")
                except Exception:
                    continue
                    
    if not results:
        return f"No definition found for '{name}'."
    return "\n".join(results)
