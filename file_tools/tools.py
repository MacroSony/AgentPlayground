import re
import os
import httpx
import json
import time

def resolve_safe_path(filepath: str) -> str:
    """Resolves a user path and ensures it stays inside AGENT_ROOT."""
    AGENT_ROOT = os.path.realpath(os.getenv("AGENT_ROOT", os.getcwd()))
    candidate = os.path.realpath(os.path.join(AGENT_ROOT, filepath))
    if candidate == AGENT_ROOT or candidate.startswith(f"{AGENT_ROOT}{os.sep}"):
        return candidate
    raise ValueError(f"Path is outside allowed root: {filepath}")

def read_file(filepath: str) -> str:
    """Reads the content of a file.

    Args:
        filepath: The path to the file relative to /app/agent.
    """
    try:
        safe_path = resolve_safe_path(filepath)
        if not os.path.exists(safe_path):
            return f"Error: File {filepath} not found."
        with open(safe_path, 'r') as f:
            content = f.read()
            if len(content) > 15000:
                return content[:15000] + "\n\n... [CONTENT TRUNCATED: File exceeds 15000 characters] ..."
            return content
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(filepath: str, content: str) -> str:
    """Writes content to a file, overwriting existing content.

    Args:
        filepath: The path to the file relative to /app/agent.
        content: The text content to write.
    """
    try:
        safe_path = resolve_safe_path(filepath)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {safe_path}"
    except Exception as e:
        return f"Error writing file: {e}"

def replace_in_file(filepath: str, old_text: str, new_text: str) -> str:
    """Replaces a specific string with another string in a file.
    
    Args:
        filepath: The path to the file relative to /app/agent.
        old_text: The exact string to find in the file.
        new_text: The string to replace it with.
    """
    try:
        if not old_text:
            return "Error: old_text cannot be empty."
        safe_path = resolve_safe_path(filepath)
        with open(safe_path, 'r') as f:
            content = f.read()
        
        if old_text not in content:
            return f"Error: The exact text '{old_text}' was not found in {safe_path}."
            
        new_content = content.replace(old_text, new_text)
        
        with open(safe_path, 'w') as f:
            f.write(new_content)
            
        return f"Successfully replaced text in {safe_path}"
    except Exception as e:
        return f"Error replacing text in file: {e}"

def list_files(directory: str) -> str:
    """Lists files and directories in a given path.

    Args:
        directory: The path to the directory relative to /app/agent.
    """
    try:
        safe_path = resolve_safe_path(directory)
        if not os.path.exists(safe_path):
            return f"Error: Path {directory} does not exist."
        if not os.path.isdir(safe_path):
            return f"Error: Path {directory} is not a directory."
        items = os.listdir(safe_path)
        output = [f"Contents of {directory}:"]
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

def search_files(directory: str, keyword: str, use_regex: bool = False) -> str:
    """Recursively searches for a keyword or regex pattern in files within a directory.

    Args:
        directory: The path to the directory relative to /app/agent.
        keyword: The string or regex pattern to search for.
        use_regex: Whether to treat the keyword as a regex pattern.
    """
    import re
    try:
        safe_dir = resolve_safe_path(directory)
        if not os.path.isdir(safe_dir):
            return f"Error: {directory} is not a valid directory."
        
        results = []
        pattern = None
        if use_regex:
            try:
                pattern = re.compile(keyword)
            except re.error as e:
                return f"Error: Invalid regex pattern: {e}"
                
        for root, _, files in os.walk(safe_dir):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if use_regex:
                            if pattern.search(content):
                                results.append(filepath)
                        else:
                            if keyword in content:
                                results.append(filepath)
                except Exception:
                    pass
        if not results:
            return f"No files containing '{keyword}' found in {directory}."
        output = [f"Found '{keyword}' in the following files:"]
        for res in results:
            rel_path = os.path.relpath(res, safe_dir)
            output.append(rel_path)
        return "\n".join(output)
    except Exception as e:
        return f"Error searching files: {e}"

def send_discord_message(message: str) -> str:
    """Sends a message to the Discord webhook.

    Args:
        message: The message text to send.
    """
    try:
        if not message:
            return "Error: Message cannot be empty."
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if not webhook_url:
            return "Error: DISCORD_WEBHOOK_URL is not set."
            
        from file_tools.tasks import list_tasks
        tasks = list_tasks()
        
        usage = get_usage()
        
        # Additional project metrics
        memory = load_memory()
        num_mem_entries = len(memory.get("entries", [])) if isinstance(memory, dict) else 0
        
        # Test results summary (if run_tests.sh was ever run and output saved, but let's just count files for now)
        test_dir = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "tests")
        num_tests = len([f for f in os.listdir(test_dir) if f.startswith("test_") and f.endswith(".py")]) if os.path.exists(test_dir) else 0

        payload = {
            "embeds": [{
                "title": "Hoshi Status Update",
                "description": message,
                "color": 0x00ff00,
                "fields": [
                    {
                        "name": "Current Tasks",
                        "value": tasks[:1024] if tasks else "No tasks.",
                        "inline": False
                    },
                    {
                        "name": "API Usage",
                        "value": usage[:1024] if usage else "Unknown usage.",
                        "inline": True
                    },
                    {
                        "name": "System Info",
                        "value": f"Tests: {num_tests} files\nMemory: {num_mem_entries} entries",
                        "inline": True
                    }
                ],
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }]
        }
        
        with httpx.Client(timeout=10.0) as client:
            response = client.post(webhook_url, json=payload)
            response.raise_for_status()
            return "Message sent successfully to Discord with status embed."
    except Exception as e:
        # Fallback to simple message if embed fails
        try:
            with httpx.Client(timeout=10.0) as client:
                client.post(webhook_url, json={"content": f"{message}\n\n(Embed failed: {e})"})
            return f"Sent fallback Discord message. Embed error: {e}"
        except Exception as e2:
            return f"Error sending message to Discord: {e2}"

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
    """Saves a dictionary to long_term_memory.json.

    Args:
        data: The dictionary to save.
    """
    try:
        if not isinstance(data, dict):
            return "Error: Memory data must be a dictionary."
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
    """Makes the agent sleep for a specified number of seconds to wait for resource budget refresh.

    Args:
        seconds: Number of seconds to sleep.
    """
    try:
        if seconds < 0:
            return "Error: Sleep duration cannot be negative."
        print(f"AGENT: Sleeping for {seconds} seconds...")
        import time
        time.sleep(seconds)
        return f"Slept for {seconds} seconds."
    except Exception as e:
        return f"Error during sleep: {e}"

def fetch_url(url: str, selector: str = None) -> str:
    """Fetches the content of a URL and returns it as text, with basic HTML stripping.
    Can optionally extract specific elements using a CSS selector.

    Args:
        url: The full URL to fetch (must include http/https).
        selector: Optional CSS selector to extract specific content (e.g., 'article', '.main-content').
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return "BeautifulSoup not installed. Please add beautifulsoup4 to requirements.txt."
        
    try:
        if not url.startswith(("http://", "https://")):
            return "Error: URL must start with http:// or https://."
            
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            response = client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # If selector is provided, try to find matching elements
            if selector:
                elements = soup.select(selector)
                if not elements:
                    return f"Error: No elements found for selector '{selector}'."
                # Create a new soup with only the matched elements
                new_soup = BeautifulSoup("", 'html.parser')
                for el in elements:
                    new_soup.append(el)
                soup = new_soup

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
def run_python(code: str) -> str:
    """Executes a block of Python code and returns the printed output and errors.

    Args:
        code: The Python code to execute. Use print() to see output.
    """
    import sys
    import io
    import contextlib
    import traceback

    if not code:
        return "Error: No code provided."

    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            exec(code, {})
        return output.getvalue()
    except Exception:
        error_msg = traceback.format_exc()
        return output.getvalue() + "\n" + error_msg

def search_web(query: str) -> str:
    """Searches the web using DuckDuckGo HTML and returns a list of results.

    Args:
        query: The search query.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return "BeautifulSoup not installed. Please add beautifulsoup4 to requirements.txt."
        
    try:
        if not query:
            return "Error: Search query cannot be empty."
            
        import urllib.parse
        import httpx
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        data = {"q": query}
        
        # Using a context manager for httpx client
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            res = client.post("https://html.duckduckgo.com/html/", data=data, headers=headers)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, 'html.parser')
            results = []
            for result in soup.find_all('div', class_='result'):
                title_tag = result.find('a', class_='result__a')
                snippet_tag = result.find('a', class_='result__snippet')
                url_tag = result.find('a', class_='result__url')
                
                if title_tag and snippet_tag and url_tag:
                    title = title_tag.get_text(strip=True)
                    snippet = snippet_tag.get_text(strip=True)
                    
                    url = url_tag.get('href', '')
                    if url.startswith('//'):
                        url = 'https:' + url
                    
                    results.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}\n")
                    
            if not results:
                return f"No results found for '{query}'."
                
            return "\n".join(results[:5])
    except Exception as e:
        return f"Error searching web: {e}"

def search_documentation(query: str) -> str:
    """Searches technical documentation and developer sites (Python, MDN, StackOverflow, etc.).

    Args:
        query: The documentation search query.
    """
    try:
        if not query:
            return "Error: Search query cannot be empty."
        
        # DuckDuckGo HTML version seems to have issues with 'site:' and 'OR' operators.
        # We'll use a more direct approach by including key domains in the query.
        domains = ["docs.python.org", "developer.mozilla.org", "stackoverflow.com", "pypi.org", "github.com"]
        full_query = f"{query} {' '.join(domains)}"
        return search_web(full_query)
    except Exception as e:
        return f"Error searching documentation: {e}"

def search_memory(query: str, top_k: int = 3) -> str:
    """Searches long-term memory using semantic search with fastembed.

    Args:
        query: The semantic search query.
        top_k: The number of top results to return.
    """
    try:
        import numpy as np
        from fastembed import TextEmbedding
        
        if not query:
            return "Error: Query cannot be empty."
            
        memory = load_memory()
        if not memory or "entries" not in memory:
            return "No memory entries found."
            
        entries = memory["entries"]
        
        model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
        # Get query embedding
        query_embedding = list(model.embed([query]))[0]
        
        # Check if all entries have embeddings
        needs_save = False
        embeddings = []
        for e in entries:
            if "embedding" in e:
                embeddings.append(np.array(e["embedding"]))
            else:
                emb = list(model.embed([e["text"]]))[0]
                e["embedding"] = emb.tolist()
                embeddings.append(emb)
                needs_save = True
        
        if needs_save:
            save_memory(memory)
        
        # Compute cosine similarities
        similarities = []
        for emb in embeddings:
            sim = np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
            similarities.append(sim)
            
        # Get top K indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for i in top_indices:
            i = int(i)
            # Add context: entry before and after if they exist
            entry_text = entries[i]['text']
            timestamp = entries[i].get('timestamp', 'Unknown Time')
            metadata = entries[i].get('metadata', {})
            
            context_before = entries[i-1]['text'] if i > 0 else ""
            context_after = entries[i+1]['text'] if i < len(entries) - 1 else ""
            
            result = f"[Score: {similarities[i]:.4f}] [Time: {timestamp}]\n"
            if metadata:
                result += f"METADATA: {json.dumps(metadata)}\n"
            if context_before:
                result += "CONTEXT BEFORE: " + context_before[-200:] + "\n"
            result += "ENTRY: " + entry_text + "\n"
            if context_after:
                result += "CONTEXT AFTER: " + context_after[:200] + "\n"
            
            results.append(result)
            
        return "\n---\n".join(results)
    except Exception as e:
        return f"Error searching memory: {e}"

def add_memory_entry(text: str, metadata: dict = None) -> str:
    """Adds a new text entry to long-term memory and pre-calculates its embedding.

    Args:
        text: The text content to store in memory.
        metadata: Optional dictionary of metadata (e.g., timestamp, tags).
    """
    try:
        import numpy as np
        from fastembed import TextEmbedding
        import time
        
        if not text:
            return "Error: Memory text cannot be empty."
            
        memory = load_memory()
        if "entries" not in memory:
            memory["entries"] = []
            
        model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        embedding = list(model.embed([text]))[0]
        
        entry = {
            "text": text,
            "embedding": embedding.tolist(),
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "metadata": metadata or {}
        }
        memory["entries"].append(entry)
        save_memory(memory)
        return f"Added memory entry: {text}"
    except Exception as e:
        return f"Error adding memory entry: {e}"

def journal_status() -> str:
    """Summarizes the current dev_log and tasks into a long-term memory entry."""
    try:
        from file_tools.tasks import list_tasks
        
        dev_log = read_file("dev_log.txt")
        tasks = list_tasks()
        
        # Simple extraction of the last 1000 chars of dev log for context
        log_context = dev_log[-1000:] if len(dev_log) > 1000 else dev_log
        
        summary_prompt = f"Summarize the following progress and task status into a concise long-term memory entry:\n\nLOG:\n{log_context}\n\nTASKS:\n{tasks}"
        
        # Since I can't easily call the model from within a tool without passing the client,
        # I will return the prompt for the agent to use, or just do a basic programmatic summary.
        # Actually, let's keep it simple for now and just store the raw recent status.
        
        entry = f"Journal Entry ({time.strftime('%Y-%m-%d %H:%M:%S')}):\nTasks: {tasks}\nRecent Log: {log_context[-300:]}"
        return add_memory_entry(entry, metadata={"type": "journal", "cycle": time.strftime('%Y-%m-%d')})
    except Exception as e:
        return f"Error journaling status: {e}"

def patch_file(filepath: str, patches: str) -> str:
    """Applies a series of SEARCH/REPLACE patches to a file.
    
    This tool is more robust than replace_in_file for multi-line changes.
    Format for patches:
    <<<<<<< SEARCH
    old code
    =======
    new code
    >>>>>>> REPLACE

    Args:
        filepath: The path to the file relative to /app/agent.
        patches: One or more SEARCH/REPLACE blocks.
    """
    try:
        safe_path = resolve_safe_path(filepath)
        if not os.path.exists(safe_path):
            return f"Error: File {filepath} not found."
            
        with open(safe_path, 'r') as f:
            content = f.read()
            
        pattern = r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
        matches = re.findall(pattern, patches, re.DOTALL)
        
        if not matches:
            return "Error: No valid SEARCH/REPLACE blocks found. Ensure the format is exact."
            
        new_content = content
        applied_count = 0
        
        for search_text, replace_text in matches:
            if search_text in new_content:
                new_content = new_content.replace(search_text, replace_text, 1)
                applied_count += 1
            else:
                return f"Error: SEARCH block not found in file:\n{search_text}"
                
        with open(safe_path, 'w') as f:
            f.write(new_content)
            
        return f"Successfully applied {applied_count} patch(es) to {filepath}."
    except Exception as e:
        return f"Error applying patches: {e}"
