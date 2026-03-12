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

def _get_discord_payload(message: str) -> dict:
    from file_tools.tasks import list_tasks
    tasks = list_tasks()
    usage = get_usage()
    memory = load_memory()
    num_mem_entries = len(memory.get("entries", [])) if isinstance(memory, dict) else 0
    test_dir = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "tests")
    num_tests = len([f for f in os.listdir(test_dir) if f.startswith("test_") and f.endswith(".py")]) if os.path.exists(test_dir) else 0

    return {
        "embeds": [{
            "title": "Hoshi Status Update",
            "description": message,
            "color": 0x00ff00,
            "fields": [
                {"name": "Current Tasks", "value": tasks[:1024] if tasks else "No tasks.", "inline": False},
                {"name": "API Usage", "value": usage[:1024] if usage else "Unknown usage.", "inline": True},
                {"name": "System Info", "value": f"Tests: {num_tests} files\nMemory: {num_mem_entries} entries", "inline": True}
            ],
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }]
    }

def send_discord_message(message: str) -> str:
    """Sends a message to the Discord webhook."""
    try:
        if not message: return "Error: Message cannot be empty."
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if not webhook_url: return "Error: DISCORD_WEBHOOK_URL is not set."
            
        payload = _get_discord_payload(message)
        with httpx.Client(timeout=10.0) as client:
            client.post(webhook_url, json=payload).raise_for_status()
            return "Message sent successfully to Discord with status embed."
    except Exception as e:
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

def _clean_soup(soup):
    for script in soup(["script", "style", "header", "footer", "nav"]):
        script.decompose()
    text = soup.get_text(separator=' ')
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk)

def fetch_url(url: str, selector: str = None, remove_selectors: list = None) -> str:
    """Fetches the content of a URL and returns it as text."""
    try:
        from bs4 import BeautifulSoup
    except ImportError: return "BeautifulSoup not installed."
        
    try:
        if not url.startswith(("http://", "https://")): return "Error: Invalid URL."
            
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = client.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            if remove_selectors:
                for rem_sel in remove_selectors:
                    for el in soup.select(rem_sel): el.decompose()
            
            if selector:
                elements = soup.select(selector)
                if not elements: return f"Error: No elements for '{selector}'."
                new_soup = BeautifulSoup("", 'html.parser')
                for el in elements: new_soup.append(el)
                soup = new_soup

            text = _clean_soup(soup)
            return (text[:15000] + "\n\n... [TRUNCATED] ...") if len(text) > 15000 else text
    except Exception as e: return f"Error fetching URL: {e}"
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

def _compute_cosine_similarity(query_emb, doc_emb):
    import numpy as np
    q_norm = np.linalg.norm(query_emb)
    d_norm = np.linalg.norm(doc_emb)
    if q_norm == 0 or d_norm == 0:
        return 0.0
    return float(np.dot(query_emb, doc_emb) / (q_norm * d_norm))

def search_memory(query: str, top_k: int = 3, threshold: float = 0.5, metadata_filter: dict = None, context_window: int = 1) -> str:
    """Searches long-term memory using semantic search with fastembed.

    Args:
        query: The semantic search query.
        top_k: The number of top results to return.
        threshold: Minimum similarity score (0.0 to 1.0).
        metadata_filter: Optional dict of key-value pairs that must match.
        context_window: Number of entries before and after to include.
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
        query_embedding = list(model.embed([query]))[0]
        
        # Filtering & Scoring
        scored_results = []
        needs_save = False
        
        for i, entry in enumerate(entries):
            # Metadata Filter
            if metadata_filter:
                match = True
                entry_meta = entry.get("metadata", {})
                for k, v in metadata_filter.items():
                    if entry_meta.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            
            # Get/Create Embedding
            if "embedding" in entry:
                doc_emb = np.array(entry["embedding"])
            else:
                doc_emb = list(model.embed([entry["text"]]))[0]
                entry["embedding"] = doc_emb.tolist()
                needs_save = True
                
            sim = _compute_cosine_similarity(query_embedding, doc_emb)
            if sim >= threshold:
                scored_results.append((sim, i))
        
        if needs_save:
            save_memory(memory)
            
        scored_results.sort(key=lambda x: x[0], reverse=True)
        top_results = scored_results[:top_k]
        
        if not top_results:
            return f"No memory entries found above threshold {threshold}."
            
        results = []
        for sim, i in top_results:
            entry = entries[i]
            res = f"[Score: {sim:.4f}] [Time: {entry.get('timestamp', 'Unknown')}]\n"
            if "metadata" in entry:
                res += f"METADATA: {json.dumps(entry['metadata'])}\n"
            
            # Flexible Context Window
            start = max(0, i - context_window)
            end = min(len(entries), i + context_window + 1)
            for ctx_idx in range(start, end):
                prefix = f"CONTEXT [{ctx_idx-i}]: " if ctx_idx != i else "ENTRY: "
                res += f"{prefix}{entries[ctx_idx]['text']}\n"
            
            results.append(res)
            
        return "\n---\n".join(results)
    except Exception as e:
        return f"Error searching memory: {e}"

def add_memory_entry(text: str, metadata: dict = None, auto_tag: bool = False) -> str:
    """Adds a new text entry to long-term memory and pre-calculates its embedding.

    Args:
        text: The text content to store in memory.
        metadata: Optional dictionary of metadata (e.g., timestamp, tags).
        auto_tag: Whether to attempt basic automatic tagging based on keywords.
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
        
        final_metadata = metadata or {}
        if auto_tag:
            tags = set(final_metadata.get("tags", []))
            keywords = {
                "task": ["task", "todo", "done", "status"],
                "project": ["project", "refactor", "tool", "loop"],
                "tech": ["ai", "gemini", "python", "scraping", "memory"],
                "git": ["git", "branch", "commit", "push", "pull"]
            }
            text_lower = text.lower()
            for tag, keys in keywords.items():
                if any(k in text_lower for k in keys):
                    tags.add(tag)
            if tags:
                final_metadata["tags"] = list(tags)

        entry = {
            "text": text,
            "embedding": embedding.tolist(),
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "metadata": final_metadata
        }
        memory["entries"].append(entry)
        save_memory(memory)
        return f"Added memory entry with tags {final_metadata.get('tags', [])}: {text[:100]}..."
    except Exception as e:
        return f"Error adding memory entry: {e}"

def list_available_tools() -> str:
    """Lists all available tools and their descriptions for the agent."""
    try:
        import inspect
        # Let's just list the ones in this file for now.
        # Use sys.modules to find the current module's functions
        import sys
        this_module = sys.modules[__name__]
        functions = inspect.getmembers(this_module, inspect.isfunction)
        
        output = ["Available Tools in file_tools/tools.py:"]
        for name, func in functions:
            if not name.startswith("_"):
                doc = inspect.getdoc(func)
                first_line = doc.splitlines()[0] if doc else "No description."
                output.append(f"- {name}: {first_line}")
        return "\n".join(output)
    except Exception as e:
        return f"Error listing tools: {e}"

def journal_status(summary: str) -> str:
    """Adds a summary of progress to long-term memory.
    
    Args:
        summary: A concise summary of recent accomplishments and status.
    """
    try:
        from file_tools.tasks import list_tasks
        tasks = list_tasks()
        entry = f"Status Report ({time.strftime('%Y-%m-%d %H:%M:%S')}):\n{summary}\n\nTasks:\n{tasks}"
        return add_memory_entry(entry, metadata={"type": "journal", "cycle": time.strftime('%Y-%m-%d')}, auto_tag=True)
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
