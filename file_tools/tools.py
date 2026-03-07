import os
import shutil

def list_files(directory: str) -> str:
    """Lists files and directories in a given path."""
    try:
        from loop import resolve_safe_path
        safe_path = resolve_safe_path(directory)
        
        if not os.path.exists(safe_path):
            return f"Error: Path {safe_path} does not exist."
            
        if not os.path.isdir(safe_path):
            return f"Error: Path {safe_path} is not a directory."
            
        items = os.listdir(safe_path)
        
        output = [f"Contents of {safe_path}:"]
        for item in items:
            item_path = os.path.join(safe_path, item)
            if os.path.isdir(item_path):
                output.append(f"[DIR]  {item}")
            else:
                size = os.path.getsize(item_path)
                output.append(f"[FILE] {item} ({size} bytes)")
                
        return "\n".join(output)
    except Exception as e:
        return f"Error listing files: {e}"

def search_files(directory: str, keyword: str) -> str:
    """Recursively searches for a keyword in files within a directory."""
    try:
        from loop import resolve_safe_path
        safe_dir = resolve_safe_path(directory)
        
        if not os.path.isdir(safe_dir):
            return f"Error: {safe_dir} is not a valid directory."
            
        results = []
        for root, _, files in os.walk(safe_dir):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if keyword in content:
                            results.append(filepath)
                except Exception:
                    # Skip files that can't be read (e.g. binary)
                    pass
                    
        if not results:
            return f"No files containing '{keyword}' found in {safe_dir}."
            
        output = [f"Found '{keyword}' in the following files:"]
        for res in results:
            # Show path relative to safe_dir for cleaner output
            rel_path = os.path.relpath(res, safe_dir)
            output.append(rel_path)
            
        return "\n".join(output)
    except Exception as e:
        return f"Error searching files: {e}"
