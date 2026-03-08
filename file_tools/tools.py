import os
import httpx
import json

def resolve_safe_path(filepath: str) -> str:
    """Resolves a user path and ensures it stays inside AGENT_ROOT."""
    AGENT_ROOT = os.path.realpath(os.getenv("AGENT_ROOT", os.getcwd()))
    candidate = os.path.realpath(os.path.join(AGENT_ROOT, filepath))
    if candidate == AGENT_ROOT or candidate.startswith(f"{AGENT_ROOT}{os.sep}"):
        return candidate
    raise ValueError(f"Path is outside allowed root: {filepath}")

def read_file(filepath: str) -> str:
    """Reads the content of a file."""
    try:
        safe_path = resolve_safe_path(filepath)
        with open(safe_path, 'r') as f:
            content = f.read()
            if len(content) > 15000:
                return content[:15000] + "\n\n... [CONTENT TRUNCATED: File exceeds 15000 characters] ..."
            return content
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(filepath: str, content: str) -> str:
    """Writes content to a file, overwriting existing content."""
    try:
        safe_path = resolve_safe_path(filepath)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {safe_path}"
    except Exception as e:
        return f"Error writing file: {e}"

def list_files(directory: str) -> str:
    """Lists files and directories in a given path."""
    try:
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
                    pass
        if not results:
            return f"No files containing '{keyword}' found in {safe_dir}."
        output = [f"Found '{keyword}' in the following files:"]
        for res in results:
            rel_path = os.path.relpath(res, safe_dir)
            output.append(rel_path)
        return "\n".join(output)
    except Exception as e:
        return f"Error searching files: {e}"

def send_discord_message(message: str) -> str:
    """Sends a message to the Discord webhook."""
    try:
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if not webhook_url:
            return "Error: DISCORD_WEBHOOK_URL is not set."
        with httpx.Client(timeout=10.0) as client:
            response = client.post(webhook_url, json={"content": message})
            response.raise_for_status()
            return "Message sent successfully to Discord."
    except Exception as e:
        return f"Error sending message to Discord: {e}"

def get_usage() -> str:
    """Fetches the current daily API usage from the moderator."""
    try:
        base_url = os.getenv("GEMINI_API_BASE_URL", "http://moderator:8000")
        agent_token = os.getenv("GEMINI_API_KEY", "dummy_key")
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{base_url}/usage", params={"key": agent_token})
            response.raise_for_status()
            data = response.json()
            output = f"Daily API Usage ({data['date']}):\n"
            output += f"- Pro Tier: {data['pro']} / {data['limits']['pro']} calls\n"
            output += f"- Flash Tier: {data['flash']} / {data['limits']['flash']} calls\n"
            return output
    except Exception as e:
        return f"Error fetching usage: {e}"

def save_memory(data: dict) -> str:
    """Saves a dictionary to long_term_memory.json."""
    try:
        with open("long_term_memory.json", "w") as f:
            json.dump(data, f)
        return "Memory saved successfully."
    except Exception as e:
        return f"Error saving memory: {e}"

def load_memory() -> dict:
    """Loads memory from long_term_memory.json. Returns empty dict if not found."""
    try:
        if os.path.exists("long_term_memory.json"):
            with open("long_term_memory.json", "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading memory: {e}")
        return {}

def sleep(seconds: int) -> str:
    """Makes the agent sleep for a specified number of seconds."""
    try:
        print(f"AGENT: Sleeping for {seconds} seconds...")
        import time
        time.sleep(seconds)
        return f"Slept for {seconds} seconds."
    except Exception as e:
        return f"Error during sleep: {e}"

def fetch_url(url: str) -> str:
    """Fetches the content of a URL and returns it as text, with basic HTML stripping."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return "BeautifulSoup not installed. Please add beautifulsoup4 to requirements.txt."
        
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            response = client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # Remove scripts and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text(separator=' ')
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            if len(text) > 10000:
                return text[:10000] + "\n\n... [CONTENT TRUNCATED] ..."
            return text
    except Exception as e:
        return f"Error fetching URL: {e}"
