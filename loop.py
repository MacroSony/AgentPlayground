from google import genai
from google.genai import types
import os
import subprocess
import time
import httpx
import json

REQUESTED_RESTART = False
MODEL_CONFIG_FILE = "active_model.txt"
AGENT_ROOT = os.path.realpath(os.getenv("AGENT_ROOT", os.getcwd()))
ALLOWED_MODELS = {
    "flash": "gemini-3-flash-preview",
    "pro": "gemini-3.1-pro-preview",
}

# 1. API Configuration
# Initialize the NEW google-genai client
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY", "dummy_key"),
    http_options={'base_url': os.getenv("GEMINI_API_BASE_URL", "http://moderator:8000")}
)

# 2. Tool Definitions
def resolve_safe_path(filepath: str) -> str:
    """Resolves a user path and ensures it stays inside AGENT_ROOT."""
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
            # Truncate content if it's too large to protect context limits
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

def execute_command(command: str) -> str:
    """Executes a CLI command in the shell and returns the output/exit code."""
    global REQUESTED_RESTART
    if command.strip() == "exit 0":
        # Run tests before allowing a restart to prevent local crash loops
        test_result = subprocess.run(
            ["python3", "-m", "unittest", "discover", "-s", "tests"],
            capture_output=True, text=True
        )
        if test_result.returncode != 0:
            return f"Restart ABORTED. Pre-restart safety checks failed. You MUST fix the code before restarting.\n\nTEST OUTPUT:\n{test_result.stderr}\n{test_result.stdout}"
        
        REQUESTED_RESTART = True
        return "Tests passed. Restart requested. Exiting with code 0 after this cycle."

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        
        # Truncate output to prevent context bloat
        def truncate_str(text: str, max_len: int = 10000) -> str:
            if text and len(text) > max_len:
                return text[:max_len] + f"\n\n... [TRUNCATED: Exceeds {max_len} chars] ..."
            return text

        output = truncate_str(result.stdout) if result.stdout else ""
        if result.stderr:
            output += f"\nSTDERR:\n{truncate_str(result.stderr)}"
        return f"Exit Code: {result.returncode}\nOutput: {output if output else '(no output)'}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command: {e}"

def switch_model(model_tier: str) -> str:
    """Switches the active Gemini model tier and requests a clean restart."""
    global REQUESTED_RESTART
    tier = model_tier.strip().lower()
    if tier not in ALLOWED_MODELS:
        return "Invalid model tier. Use 'flash' or 'pro'."

    model_name = ALLOWED_MODELS[tier]
    try:
        with open(MODEL_CONFIG_FILE, "w") as f:
            f.write(model_name)
        REQUESTED_RESTART = True
        return f"Model switched to {model_name}. Restart requested."
    except Exception as e:
        return f"Error switching model: {e}"

def get_active_model_name() -> str:
    """Loads active model from disk, defaulting to pro."""
    try:
        if os.path.exists(MODEL_CONFIG_FILE):
            with open(MODEL_CONFIG_FILE, "r") as f:
                configured_model = f.read().strip()
                return configured_model
    except Exception:
        pass
    return ALLOWED_MODELS["pro"]

def sleep(seconds: int) -> str:
    """Makes the agent sleep for a specified number of seconds. Use this to wait for resource refresh."""
    try:
        print(f"AGENT: Sleeping for {seconds} seconds...")
        time.sleep(seconds)
        return f"Slept for {seconds} seconds."
    except Exception as e:
        return f"Error during sleep: {e}"


def send_discord_message(message: str) -> str:
    """Sends a message to the Discord webhook."""
    try:
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if not webhook_url:
            return "Error: DISCORD_WEBHOOK_URL is not set."
            
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                webhook_url,
                json={"content": message}
            )
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
            response = client.get(
                f"{base_url}/usage",
                params={"key": agent_token}
            )
            response.raise_for_status()
            data = response.json()
            
            output = f"Daily API Usage ({data['date']}):\n"
            output += f"- Pro Tier: {data['pro']} / {data['limits']['pro']} calls\n"
            output += f"- Flash Tier: {data['flash']} / {data['limits']['flash']} calls\n"
            return output
    except Exception as e:
        return f"Error fetching usage: {e}"

# 3. System Instructions
def get_system_instruction() -> str:
    """Reads creater's note and checks for past failures."""
    try:
        with open("creaters_note.md", "r") as f:
            instruction = f.read()
    except FileNotFoundError:
        instruction = "You are an autonomous AI. Build your own capabilities."
    
    try:
        if os.path.exists("crash_report.txt"):
            with open("crash_report.txt", "r") as f:
                crash_log = f.read().strip()
                if crash_log:
                    instruction += (
                        f"\n\nCRITICAL SYSTEM ALERT: Your previous code execution crashed with the following error:\n"
                        f"{crash_log}\n"
                        f"Please analyze your files and fix this issue immediately."
                    )
            # We don't clear it here anymore; supervisor handles it or we do it after successful action
    except Exception:
        pass
        
    return instruction

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

# 4. The Core Agentic Loop
def main():
    print("AGENT: Booting cognitive loop...")
    
    active_model = get_active_model_name()
    print(f"AGENT: Active model: {active_model}")

    # Register tools using the new SDK format
    tools = [read_file, write_file, execute_command, switch_model, sleep, get_usage, send_discord_message, save_memory, load_memory]
    config = types.GenerateContentConfig(
        system_instruction=get_system_instruction(),
        tools=tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
    )

    # Initialize chat to manage context better
    loop_count = 0
    chat = client.chats.create(
        model=active_model,
        config=config
    )
    
    while True:
        loop_count += 1
        print(f"\n--- Cognitive Cycle {loop_count} ---")
        
        # We can dynamically adjust history length if it gets too long
        # The genai SDK chat object manages history automatically, 
        # but for safety against context limits, we might truncate in the future.
        # For now, let's just use the chat object directly.
        
        prompt = (
            "Status Check: Analyze your current state and dev log. Take the next logical step. "
            "If you've completed a major task, summarize it in your log. "
            "If you need to restart after a code change, call execute_command('exit 0')."
        )
        
        try:
            print("AGENT: Thinking...")
            response = chat.send_message(prompt)
            
            # Print thoughts (text parts)
            thought = "".join([part.text for part in response.candidates[0].content.parts if part.text])
            print(f"AGENT: Action completed.\nThoughts: {thought}")
            
            # Clear crash report if we've successfully reached this point
            if os.path.exists("crash_report.txt"):
                try:
                    open("crash_report.txt", "w").close()
                except Exception:
                    pass

            if REQUESTED_RESTART:
                print("AGENT: Restart requested. Exiting...")
                return
            
            # Adaptive sleep: longer if no action taken, shorter if busy
            time.sleep(10)
            
        except Exception as e:
            error_str = str(e)
            print(f"AGENT: Error: {error_str}")
            
            # Handle rate limits / resource exhaustion (429)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print("AGENT: Budget exhausted. Sleeping for 15 minutes...")
                time.sleep(900)
            else:
                # Standard error sleep
                print("AGENT: Encountered an error. Retrying in 30 seconds...")
                time.sleep(30)

if __name__ == "__main__":
    main()