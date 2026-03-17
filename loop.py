from google import genai
from google.genai import types
import os
import subprocess
import time

# Import tools from file_tools/tools.py
from file_tools.tools import (
    read_file, write_file, replace_in_file, list_files, search_files,
    send_discord_message, get_usage, save_memory, load_memory, sleep, fetch_url,
    run_python, search_web, search_documentation, search_memory, add_memory_entry, patch_file, journal_status,
    list_available_tools
)
from file_tools.tasks import add_task, list_tasks, update_task_status
from file_tools.git_tools import git_status, git_checkout, git_commit, git_push, git_pull
from file_tools.ast_tools import analyze_python_file, summarize_project, find_definition
from file_tools.rss_tools import parse_rss_feed, summarize_rss_entry
from file_tools.health_tools import check_code_health
from file_tools.research_tools import deep_search
from file_tools.communication_tools import reply_to_user
from file_tools.reporting_tools import generate_status_report, run_test_suite

REQUESTED_RESTART = False
MODEL_CONFIG_FILE = "active_model.txt"
AGENT_ROOT = os.path.realpath(os.getenv("AGENT_ROOT", os.getcwd()))
ALLOWED_MODELS = {
    "flash": "gemini-3-flash-preview",
    "pro": "gemini-3.1-pro-preview",
}

# Setup environment for fastembed
os.environ["HF_HOME"] = os.path.join(AGENT_ROOT, ".cache/huggingface")
os.environ["FASTEMBED_CACHE_PATH"] = os.path.join(AGENT_ROOT, ".cache/fastembed")
os.environ["TMPDIR"] = os.path.join(AGENT_ROOT, ".cache/tmp")
os.makedirs(os.environ["HF_HOME"], exist_ok=True)
os.makedirs(os.environ["FASTEMBED_CACHE_PATH"], exist_ok=True)
os.makedirs(os.environ["TMPDIR"], exist_ok=True)

# 1. API Configuration
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY", "dummy_key"),
    http_options={'base_url': os.getenv("GEMINI_API_BASE_URL", "http://moderator:8000")}
)

# 2. Tool Definitions that depend on loop globals
def execute_command(command: str) -> str:
    """Executes a CLI command in the shell and returns the output/exit code."""
    global REQUESTED_RESTART
    if command.strip() == "exit 0":
        test_result = subprocess.run(["./run_tests.sh"], capture_output=True, text=True)
        if test_result.returncode != 0:
            return f"Restart ABORTED. Pre-restart safety checks failed. You MUST fix the code before restarting.\n\nTEST OUTPUT:\n{test_result.stderr}\n{test_result.stdout}"
        
        REQUESTED_RESTART = True
        return "Tests passed. Restart requested. Exiting with code 0 after this cycle."

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        
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
    """Loads active model from disk, defaulting to pro tier."""
    try:
        if os.path.exists(MODEL_CONFIG_FILE):
            with open(MODEL_CONFIG_FILE, "r") as f:
                return f.read().strip()
    except Exception:
        pass
    return ALLOWED_MODELS["pro"]

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
    except Exception:
        pass
        
    return instruction

def get_tools():
    """Returns the list of tools available to the agent."""
    return [
        read_file, write_file, replace_in_file, list_files, search_files,
        execute_command, switch_model, sleep, get_usage, send_discord_message,
        save_memory, load_memory, fetch_url, run_python, search_web,
        search_documentation, search_memory, add_memory_entry, patch_file,
        journal_status, add_task, list_tasks, update_task_status,
        git_status, git_checkout, git_commit, git_push, git_pull,
        analyze_python_file, summarize_project, find_definition,
        parse_rss_feed, summarize_rss_entry, check_code_health,
        deep_search, list_available_tools, reply_to_user,
        generate_status_report, run_test_suite
    ]

def initialize_chat(model_name):
    """Initializes the GenAI chat with the system instruction and tools."""
    config = types.GenerateContentConfig(
        system_instruction=get_system_instruction(),
        tools=get_tools(),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
    )
    return client.chats.create(model=model_name, config=config)

def update_heartbeat():
    """Updates the heartbeat file with current timestamp."""
    try:
        with open("heartbeat.txt", "w") as f:
            f.write(str(time.time()))
    except Exception:
        pass

def check_background_processes():
    """Checks if background processes are running and restarts them if necessary."""
    import psutil
    AGENT_ROOT = os.path.realpath(os.getenv("AGENT_ROOT", os.getcwd()))
    python_exe = os.path.join(AGENT_ROOT, ".venv/bin/python")
    if not os.path.exists(python_exe):
        python_exe = "python3"

    processes_to_check = {
        "dashboard.py": "dashboard.py",
        "hoshi_bot.py": "hoshi_bot.py"
    }
    
    running_processes = []
    for p in psutil.process_iter(['pid', 'cmdline']):
        try:
            if p.info['cmdline']:
                running_processes.append(' '.join(p.info['cmdline']))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    for name, script in processes_to_check.items():
        if name == "hoshi_bot.py" and not os.getenv("DISCORD_BOT_TOKEN"):
            continue # Don't try to restart bot if no token
            
        is_running = any(script in cmd for cmd in running_processes)
        if not is_running:
            print(f"AGENT: Self-healing: Restarting {name}...")
            stdout_file = "dashboard_stdout.txt" if "dashboard" in name else "discord_bot_stdout.txt"
            stderr_file = "dashboard_stderr.txt" if "dashboard" in name else "discord_bot_stderr.txt"
            try:
                subprocess.Popen([python_exe, script], 
                                 stdout=open(stdout_file, "a"), 
                                 stderr=open(stderr_file, "a"))
            except Exception as e:
                print(f"AGENT: Failed to restart {name}: {e}")

def _process_inbox(prompt):
    """Helper function to consolidate and read inbox messages."""
    inbox_path = "inbox.txt"
    processing_path = "inbox_processing.txt"
    inbox_content = ""
    
    if os.path.exists(inbox_path) and os.path.getsize(inbox_path) > 0:
        try:
            with open(inbox_path, "r") as f_in, open(processing_path, "a") as f_out:
                f_out.write(f_in.read())
            open(inbox_path, "w").close()
        except Exception as e:
            print(f"AGENT: Error consolidating inbox: {e}")
            
    if os.path.exists(processing_path):
        try:
            with open(processing_path, "r") as f:
                inbox_content = f.read().strip()
        except Exception:
            pass

    if inbox_content:
        prompt += f"\n\n--- INCOMING MESSAGES FROM CREATER ---\n{inbox_content}\n--------------------------------------\n(Please read these messages. When you have processed them, clear the processing inbox by calling write_file('inbox_processing.txt', ''))"
        print("AGENT: Found messages in inbox.")
        
    return prompt

def run_cycle(chat, loop_count):
    """Executes a single cognitive cycle."""
    update_heartbeat()
    
    if loop_count % 10 == 0:
        check_background_processes()
        
    print(f"\n--- Cognitive Cycle {loop_count} ---")
    prompt = (
        "Status Check: Analyze your current state and dev log. Take the next logical step. "
        "If you've completed a major task, summarize it in your log. "
        "If you need to restart after a code change, call execute_command('exit 0')."
    )
    
    prompt = _process_inbox(prompt)

    print("AGENT: Thinking...")
    response = chat.send_message(prompt)
    
    thought = "".join([part.text for part in response.candidates[0].content.parts if hasattr(part, 'text') and part.text])
    print(f"AGENT: Action completed.\nThoughts: {thought}")
    
    if os.path.exists("crash_report.txt"):
        try:
            open("crash_report.txt", "w").close()
        except Exception:
            pass
    
    return REQUESTED_RESTART

# 4. The Core Agentic Loop
def start_background_processes():
    """Starts background processes like the Flask dashboard."""
    try:
        # Kill existing dashboard process if running to free port 5000
        import psutil
        for p in psutil.process_iter(['pid', 'cmdline']):
            try:
                if p.info['cmdline'] and 'dashboard.py' in ' '.join(p.info['cmdline']):
                    p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(1)
        
        # Use the venv python to ensure dependencies are available
        python_exe = os.path.join(AGENT_ROOT, ".venv/bin/python")
        if not os.path.exists(python_exe):
            python_exe = "python3" # Fallback
            
        # Start dashboard.py in the background
        subprocess.Popen([python_exe, "dashboard.py"], 
                         stdout=open("dashboard_stdout.txt", "a"), 
                         stderr=open("dashboard_stderr.txt", "a"))
        print(f"AGENT: Flask dashboard starting with {python_exe}...")
        
        # Kill existing hoshi_bot process if running
        for p in psutil.process_iter(['pid', 'cmdline']):
            try:
                if p.info['cmdline'] and 'hoshi_bot.py' in ' '.join(p.info['cmdline']):
                    p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Start hoshi_bot.py in the background if token exists
        if os.getenv("DISCORD_BOT_TOKEN"):
            subprocess.Popen([python_exe, "hoshi_bot.py"], 
                             stdout=open("discord_bot_stdout.txt", "a"), 
                             stderr=open("discord_bot_stderr.txt", "a"))
            print(f"AGENT: Discord bot starting with {python_exe}...")
    except Exception as e:
        print(f"AGENT: Error starting background processes: {e}")

def _check_and_switch_model(active_model):
    """Proactively checks usage and switches model if exhausted."""
    usage_text = get_usage()
    import re
    m_pro = re.search(r"Pro Tier: (\d+)", usage_text)
    m_flash = re.search(r"Flash Tier: (\d+)", usage_text)
    
    pro_exhausted = m_pro and int(m_pro.group(1)) >= 200
    flash_exhausted = m_flash and int(m_flash.group(1)) >= 800
    
    if pro_exhausted and flash_exhausted:
        print("AGENT: Both model tiers exhausted. Proceeding with caution.")
    elif pro_exhausted and active_model == ALLOWED_MODELS["pro"]:
        print("AGENT: Pro tier exhausted. Proactively switching to Flash.")
        with open(MODEL_CONFIG_FILE, "w") as f:
            f.write(ALLOWED_MODELS["flash"])
        return ALLOWED_MODELS["flash"]
    elif flash_exhausted and active_model == ALLOWED_MODELS["flash"]:
        print("AGENT: Flash tier exhausted. Proactively switching to Pro.")
        with open(MODEL_CONFIG_FILE, "w") as f:
            f.write(ALLOWED_MODELS["pro"])
        return ALLOWED_MODELS["pro"]
    return active_model

def _handle_exhaustion(active_model):
    """Handles rate limit exhaustion logic."""
    exhaustion_file = ".exhaustion_log.txt"
    current_time = time.time()
    last_exhausted = 0
    try:
        if os.path.exists(exhaustion_file):
            with open(exhaustion_file, "r") as f:
                last_exhausted = float(f.read().strip())
    except Exception:
        pass
    
    if current_time - last_exhausted < 3600:
        print("AGENT: Both models likely exhausted. Sleeping for 1 hour...")
        time.sleep(3600)
    else:
        print("AGENT: Budget exhausted. Switching model...")
        with open(exhaustion_file, "w") as f:
            f.write(str(current_time))
        if active_model == ALLOWED_MODELS["flash"]:
            switch_model("pro")
        else:
            switch_model("flash")

def main():
    print("AGENT: Booting cognitive loop...")
    start_background_processes()
    active_model = _check_and_switch_model(get_active_model_name())
    print(f"AGENT: Active model: {active_model}")
    chat = initialize_chat(active_model)
    loop_count = 0
    
    while True:
        loop_count += 1
        try:
            if run_cycle(chat, loop_count):
                print("AGENT: Restart requested. Exiting...")
                return
            time.sleep(10)
        except Exception as e:
            _handle_loop_error(e, active_model)

def _handle_loop_error(e, active_model):
    error_str = str(e)
    print(f"AGENT: Error: {error_str}")
    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
        if "SYSTEM OVERRIDE" in error_str:
            _handle_exhaustion(active_model)
            # Exiting happens naturally if exhaustion switches model, or we loop if sleeping
        else:
            print("AGENT: Rate limit hit (likely transient). Sleeping for 30 seconds...")
            time.sleep(30)
    else:
        print("AGENT: Encountered an error. Retrying in 30 seconds...")
        time.sleep(30)

if __name__ == "__main__":
    main()
