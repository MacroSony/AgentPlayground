import os
import ast
import re

def check_code_health(directory: str = ".") -> str:
    """Scans the codebase for TODOs, FIXMEs, and potential code quality issues.
    
    Args:
        directory: The directory to scan.
    """
    # Resolve against CWD first to handle test runners changing AGENT_ROOT
    target_dir = os.path.realpath(directory)
    
    markers = ["TODO", "FIXME", "BUG", "HACK"]
    results = {
        "markers": [],
        "bare_excepts": [],
        "unsafe_calls": [], # eval, exec
        "complexity_issues": [] # Large functions
    }
    
    for root, dirs, files in os.walk(target_dir):
        # Filter out ignored directories in-place to prevent os.walk from entering them
        dirs[:] = [d for d in dirs if d not in [".git", ".venv", "__pycache__", ".cache", ".github", ".fastembed_cache"]]
            
        for file in files:
            if not file.endswith(".py"):
                continue
                
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, target_dir)
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.splitlines()
                    
                    # 1. Search for markers
                    for i, line in enumerate(lines):
                        for marker in markers:
                            if marker in line:
                                results["markers"].append(f"{rel_path}:{i+1}: {line.strip()}")
                                
                    # 2. Structural analysis using AST
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        # Bare excepts
                        if isinstance(node, ast.ExceptHandler) and node.type is None:
                            results["bare_excepts"].append(f"{rel_path}:{node.lineno}: Bare except block found.")
                        
                        # Unsafe calls
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                            if node.func.id in ["eval", "exec"]:
                                results["unsafe_calls"].append(f"{rel_path}:{node.lineno}: Use of '{node.func.id}' detected.")
                        
                        # Function length
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            length = (node.end_lineno - node.lineno) if hasattr(node, "end_lineno") else 0
                            if length > 50:
                                results["complexity_issues"].append(f"{rel_path}:{node.lineno}: Function '{node.name}' is long ({length} lines).")
                                
            except Exception as e:
                results["markers"].append(f"Error processing {rel_path}: {e}")

    # Format Output
    output = ["### Code Health Report ###\n"]
    
    if results["markers"]:
        output.append("#### Markers (TODO/FIXME/etc) ####")
        output.extend(results["markers"])
        output.append("")
        
    if results["bare_excepts"]:
        output.append("#### Potential Issues: Bare Excepts ####")
        output.extend(results["bare_excepts"])
        output.append("")
        
    if results["unsafe_calls"]:
        output.append("#### Potential Issues: Unsafe Calls (eval/exec) ####")
        output.extend(results["unsafe_calls"])
        output.append("")
        
    if results["complexity_issues"]:
        output.append("#### Complexity: Large Functions (>50 lines) ####")
        output.extend(results["complexity_issues"])
        output.append("")
        
    if not any(results.values()):
        return "No issues or markers found. Code looks healthy!"
        
    return "\n".join(output)
