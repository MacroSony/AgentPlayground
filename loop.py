from google import genai
from google.genai import types
import os
import subprocess
import time

# Import tools from file_tools/tools.py
from file_tools.tools import (
    read_file, write_file, replace_in_file, list_files, search_files,
    send_discord_message, get_usage, save_memory, load_memory, sleep, fetch_url,
    run_python, search_web
)
from file_tools.tasks import add_task, list_tasks, update_task_status

REQUESTED_RESTART = False
MODEL_CONFIG_FILE = "active_model.txt"
AGENT_ROOT = os.path.realpath(os.getenv("AGENT_ROOT", os.getcwd()))
ALLOWED_MODELS = {
    "flash": "gemini-3-flash-preview",
    "pro": "gemini-3.1-pro-preview",
}

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

# 4. The Core Agentic Loop
def main():
    print("AGENT: Booting cognitive loop...")
    
    active_model = get_active_model_name()
    print(f"AGENT: Active model: {active_model}")

    tools = [
        read_file, write_file, replace_in_file, list_files, search_files, 
        execute_command, switch_model, sleep, get_usage, 
        send_discord_message, save_memory, load_memory, fetch_url, run_python,
        search_web, add_task, list_tasks, update_task_status
    ]
    
    config = types.GenerateContentConfig(
        system_instruction=get_system_instruction(),
        tools=tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
    )

    loop_count = 0
    chat = client.chats.create(
        model=active_model,
        config=config
    )
    
    while True:
        loop_count += 1
        print(f"\n--- Cognitive Cycle {loop_count} ---")
        
        prompt = (
            "Status Check: Analyze your current state and dev log. Take the next logical step. "
            "If you've completed a major task, summarize it in your log. "
            "If you need to restart after a code change, call execute_command('exit 0')."
        )
        
        try:
            print("AGENT: Thinking...")
            response = chat.send_message(prompt)
            
            thought = "".join([part.text for part in response.candidates[0].content.parts if part.text])
            print(f"AGENT: Action completed.\nThoughts: {thought}")
            
            if os.path.exists("crash_report.txt"):
                try:
                    open("crash_report.txt", "w").close()
                except Exception:
                    pass

            if REQUESTED_RESTART:
                print("AGENT: Restart requested. Exiting...")
                return
            
            time.sleep(10)
            
        except Exception as e:
            error_str = str(e)
            print(f"AGENT: Error: {error_str}")
            
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print("AGENT: Budget exhausted. Sleeping for 15 minutes...")
                time.sleep(900)
            else:
                print("AGENT: Encountered an error. Retrying in 30 seconds...")
                time.sleep(30)

if __name__ == "__main__":
    main()
