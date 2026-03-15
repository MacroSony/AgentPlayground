from flask import Flask, jsonify, render_template_string, request, redirect, url_for
import json
import os

app = Flask(__name__)
AGENT_ROOT = os.getenv("AGENT_ROOT", os.getcwd())
TASKS_FILE = os.path.join(AGENT_ROOT, "tasks.json")
INBOX_FILE = os.path.join(AGENT_ROOT, "inbox.txt")
CHAT_LOG = os.path.join(AGENT_ROOT, "chat_log.txt")

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    return []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hoshi Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 20px; }
        h1 { color: #2c3e50; }
        .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .task-list { list-style: none; padding: 0; }
        .task-item { border-bottom: 1px solid #eee; padding: 10px 0; }
        .task-item:last-child { border-bottom: none; }
        .status-todo { color: #f39c12; font-weight: bold; }
        .status-done { color: #27ae60; font-weight: bold; }
        .status-blocked { color: #e74c3c; font-weight: bold; }
        .stat-card { display: inline-block; width: 140px; text-align: center; border-radius: 8px; background: #ecf0f1; margin: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-label { font-size: 12px; color: #7f8c8d; display: block; }
        .stat-value { font-size: 20px; font-weight: bold; color: #2980b9; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Hoshi Agent Dashboard</h1>
        <div id="stats">
            <div class="stat-card">
                <span class="stat-label">CPU Usage</span>
                <span class="stat-value">{{ cpu }}%</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">Memory RSS</span>
                <span class="stat-value">{{ memory }} MB</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">API (Pro)</span>
                <span class="stat-value">{{ pro_usage }} / 200</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">API (Flash)</span>
                <span class="stat-value">{{ flash_usage }} / 800</span>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h2>Send Message to Hoshi</h2>
        <form action="/send_message" method="post">
            <textarea name="message" rows="4" style="width: 100%; border-radius: 4px; border: 1px solid #ddd; padding: 10px;" placeholder="Type your message here..."></textarea>
            <br><br>
            <button type="submit" style="background-color: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">Send to Inbox</button>
        </form>
    </div>

    <div class="card">
        <h2>Active Tasks</h2>
        <ul class="task-list">
            {% for task in tasks %}
            <li class="task-item">
                <strong>ID: {{ task.id }}</strong> - {{ task.description }}
                <span class="status-{{ task.status.lower() }}">[{{ task.status.upper() }}]</span>
            </li>
            {% endfor %}
        </ul>
    </div>

    <script>
        // Auto-refresh the page every 30 seconds
        setTimeout(() => {
            location.reload();
        }, 30000);
        
        // Scroll chat to bottom
        const chatLog = document.getElementById('chat-log');
        if (chatLog) {
            chatLog.scrollTop = chatLog.scrollHeight;
        }
    </script>
</body>
</html>
"""

def get_usage_stats():
    # Helper to parse usage from moderator or file
    from file_tools.tools import get_usage
    usage_text = get_usage()
    pro = 0
    flash = 0
    import re
    m_pro = re.search(r"Pro Tier: (\d+)", usage_text)
    m_flash = re.search(r"Flash Tier: (\d+)", usage_text)
    if m_pro: pro = int(m_pro.group(1))
    if m_flash: flash = int(m_flash.group(1))
    return pro, flash

def get_system_stats():
    import psutil
    process = psutil.Process(os.getpid())
    return psutil.cpu_percent(), round(process.memory_info().rss / 1024 / 1024, 2)

def load_chat():
    if os.path.exists(CHAT_LOG):
        with open(CHAT_LOG, "r") as f:
            return f.readlines()[-50:] # Last 50 messages
    return []

@app.route("/")
def index():
    tasks = load_tasks()
    pro, flash = get_usage_stats()
    cpu, mem = get_system_stats()
    chat_entries = load_chat()
    return render_template_string(HTML_TEMPLATE, tasks=tasks, pro_usage=pro, flash_usage=flash, cpu=cpu, memory=mem, chat_entries=chat_entries)

@app.route("/send_message", methods=["POST"])
def send_message():
    message = request.form.get("message")
    if message:
        with open(INBOX_FILE, "a") as f:
            f.write(f"WEB_INTERFACE: {message}\n")
        # Also log to chat_log for display
        import time
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(CHAT_LOG, "a") as f:
            f.write(f"[{timestamp}] User: {message}\n")
    return redirect(url_for("index"))

@app.route("/api/tasks")
def api_tasks():
    return jsonify(load_tasks())

if __name__ == "__main__":
    # Note: Running on port 5000 inside the container.
    app.run(host="0.0.0.0", port=5000)
