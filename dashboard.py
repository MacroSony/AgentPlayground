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
        body { font-family: 'Inter', 'Segoe UI', Tahoma, sans-serif; background-color: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; line-height: 1.6; }
        h1, h2 { color: #f8fafc; font-weight: 600; margin-top: 0; }
        .container { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 2fr 1fr; gap: 24px; }
        .card { background: #1e293b; padding: 24px; margin-bottom: 24px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); }
        .task-list { list-style: none; padding: 0; margin: 0; }
        .task-item { border-bottom: 1px solid #334155; padding: 16px 0; transition: background-color 0.2s; }
        .task-item:hover { background-color: #334155; border-radius: 8px; padding-left: 10px; padding-right: 10px; margin-left: -10px; margin-right: -10px; }
        .task-item:last-child { border-bottom: none; }
        .status-badge { display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-right: 8px; }
        .status-todo { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
        .status-in_progress { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
        .status-done { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .status-blocked { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
        .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-top: 24px; }
        .stat-card { text-align: center; border-radius: 12px; background: #0f172a; padding: 20px; border: 1px solid #334155; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2); }
        .stat-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; font-weight: 600; display: block; margin-bottom: 8px; letter-spacing: 0.05em; }
        .stat-value { font-size: 28px; font-weight: 700; color: #38bdf8; }
        .chat-container { height: 500px; overflow-y: auto; background: #0f172a; border: 1px solid #334155; padding: 16px; border-radius: 8px; margin-bottom: 20px; font-family: 'Fira Code', 'Courier New', Courier, monospace; font-size: 14px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3); scroll-behavior: smooth; }
        .chat-entry { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px dashed #334155; }
        .chat-entry:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        .timestamp { color: #64748b; font-size: 12px; margin-right: 8px; }
        .user-tag { color: #f43f5e; font-weight: 700; }
        .hoshi-tag { color: #38bdf8; font-weight: 700; }
        .system-tag { color: #10b981; font-weight: 700; }
        textarea { width: 100%; border-radius: 8px; border: 1px solid #475569; padding: 16px; background: #1e293b; color: #f8fafc; box-sizing: border-box; resize: vertical; font-family: inherit; font-size: 15px; outline: none; transition: border-color 0.2s; }
        textarea:focus { border-color: #38bdf8; }
        button { background-color: #0ea5e9; color: white; border: none; padding: 14px 28px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 15px; transition: all 0.2s; box-shadow: 0 4px 6px -1px rgba(14, 165, 233, 0.4); }
        button:hover { background-color: #0284c7; transform: translateY(-1px); box-shadow: 0 6px 8px -1px rgba(14, 165, 233, 0.5); }
        button:active { transform: translateY(0); box-shadow: 0 2px 4px -1px rgba(14, 165, 233, 0.4); }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0f172a; border-radius: 4px; }
        ::-webkit-scrollbar-thumb { background: #475569; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #64748b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="main-content">
            <div class="card">
                <h1>Hoshi Agent Dashboard</h1>
                <div class="stat-grid">
                    <div class="stat-card">
                        <span class="stat-label">System CPU</span>
                        <span class="stat-value">{{ cpu }}%</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">Memory RSS</span>
                        <span class="stat-value">{{ memory }} MB</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">Pro Usage</span>
                        <span class="stat-value">{{ pro_usage }}/200</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">Flash Usage</span>
                        <span class="stat-value">{{ flash_usage }}/800</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">Active Model</span>
                        <span class="stat-value" style="font-size: 14px;">{{ active_model }}</span>
                    </div>
                </div>

                <div style="margin-top: 24px;">
                    <h2>Sentiment Overview (Last 100)</h2>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <div style="flex-grow: 1; height: 24px; background: #334155; border-radius: 12px; overflow: hidden; display: flex;">
                            {% if sentiment.total > 0 %}
                                <div style="width: {{ (sentiment.positive / sentiment.total * 100)|round }}%; background: #10b981;" title="Positive: {{ sentiment.positive }}"></div>
                                <div style="width: {{ (sentiment.neutral / sentiment.total * 100)|round }}%; background: #64748b;" title="Neutral: {{ sentiment.neutral }}"></div>
                                <div style="width: {{ (sentiment.negative / sentiment.total * 100)|round }}%; background: #f43f5e;" title="Negative: {{ sentiment.negative }}"></div>
                            {% else %}
                                <div style="width: 100%; background: #334155; text-align: center; font-size: 12px; color: #94a3b8;">No data</div>
                            {% endif %}
                        </div>
                        <div style="font-size: 13px; min-width: 120px; text-align: right;">
                            <span style="color: #10b981;">{{ sentiment.positive }}</span> / 
                            <span style="color: #94a3b8;">{{ sentiment.neutral }}</span> / 
                            <span style="color: #f43f5e;">{{ sentiment.negative }}</span>
                        </div>
                    </div>
                </div>
                <div style="margin-top: 20px; display: flex; gap: 10px;">
                    <form action="/switch_model" method="post" style="display: inline;">
                        <input type="hidden" name="tier" value="pro">
                        <button type="submit" style="background-color: #7c3aed; padding: 8px 16px; font-size: 13px;">Switch to Pro</button>
                    </form>
                    <form action="/switch_model" method="post" style="display: inline;">
                        <input type="hidden" name="tier" value="flash">
                        <button type="submit" style="background-color: #059669; padding: 8px 16px; font-size: 13px;">Switch to Flash</button>
                    </form>
                    <form action="/restart_agent" method="post" style="display: inline; margin-left: auto;">
                        <button type="submit" style="background-color: #dc2626; padding: 8px 16px; font-size: 13px;">Restart Agent</button>
                    </form>
                </div>
            </div>

            <div class="card">
                <h2>System Logs</h2>
                <div class="chat-container" id="system-logs" style="height: 300px; font-size: 12px; background: #020617;">
                    <pre id="logs-content" style="margin: 0; color: #94a3b8;"></pre>
                </div>
            </div>

            <div class="card">
                <h2>Communication</h2>
                <div class="chat-container" id="chat-log">
                    {% for entry in chat_entries %}
                    <div class="chat-entry">
                        {% if 'Hoshi:' in entry %}
                            {% set parts = entry.split('Hoshi:', 1) %}
                            <span class="timestamp">{{ parts[0] }}</span><span class="hoshi-tag">Hoshi:</span>{{ parts[1] }}
                        {% elif 'User:' in entry %}
                            {% set parts = entry.split('User:', 1) %}
                            <span class="timestamp">{{ parts[0] }}</span><span class="user-tag">User:</span>{{ parts[1] }}
                        {% else %}
                            <span class="system-tag">{{ entry }}</span>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
                <form action="/send_message" method="post">
                    <textarea name="message" rows="3" placeholder="Send a message to Hoshi's inbox..."></textarea>
                    <br><br>
                    <button type="submit">Send Message</button>
                </form>
            </div>
        </div>

        <div class="sidebar">
            <div class="card">
                <h2>Active Tasks</h2>
                <ul class="task-list">
                    {% for task in tasks %}
                    <li class="task-item">
                        <div style="margin-bottom: 5px;">
                            <span class="status-badge status-{{ task.status.lower().replace(' ', '_') }}">{{ task.status.upper() }}</span>
                            <small class="timestamp" style="float: right;">ID: #{{ task.id }}</small>
                        </div>
                        <div style="margin-top: 8px;">{{ task.description }}</div>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
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
        
        // Auto-refresh tasks list via API without full page reload
        async function refreshTasks() {
            try {
                const response = await fetch('/api/tasks');
                const tasks = await response.json();
                const taskList = document.querySelector('.task-list');
                
                let newHtml = '';
                for (const task of tasks) {
                    const statusClass = task.status.toLowerCase().replace(' ', '_');
                    newHtml += `
                        <li class="task-item">
                            <div style="margin-bottom: 5px;">
                                <span class="status-badge status-${statusClass}">${task.status.toUpperCase()}</span>
                                <small class="timestamp" style="float: right;">ID: #${task.id}</small>
                            </div>
                            <div style="margin-top: 8px;">${task.description}</div>
                        </li>
                    `;
                }
                
                if (taskList && taskList.innerHTML !== newHtml) {
                    taskList.innerHTML = newHtml;
                }
            } catch (e) {
                console.error("Failed to fetch tasks", e);
            }
        }
        
        async function refreshLogs() {
            try {
                const response = await fetch('/api/logs');
                const data = await response.json();
                const logContainer = document.getElementById('chat-log');
                
                let newHtml = '';
                for (const entry of data.entries) {
                    if (entry.includes('Hoshi:')) {
                        const parts = entry.split('Hoshi:', 1);
                        newHtml += `<div class="chat-entry"><span class="timestamp">${parts[0]}</span><span class="hoshi-tag">Hoshi:</span>${entry.split('Hoshi:', 2)[1]}</div>`;
                    } else if (entry.includes('User:')) {
                        const parts = entry.split('User:', 1);
                        newHtml += `<div class="chat-entry"><span class="timestamp">${parts[0]}</span><span class="user-tag">User:</span>${entry.split('User:', 2)[1]}</div>`;
                    } else {
                        newHtml += `<div class="chat-entry"><span class="system-tag">${entry}</span></div>`;
                    }
                }
                
                if (logContainer && logContainer.innerHTML !== newHtml) {
                    const atBottom = logContainer.scrollHeight - logContainer.scrollTop <= logContainer.clientHeight + 10;
                    logContainer.innerHTML = newHtml;
                    if (atBottom) {
                        logContainer.scrollTop = logContainer.scrollHeight;
                    }
                }
            } catch (e) {
                console.error("Failed to fetch logs", e);
            }
        }

        async function refreshSystemLogs() {
            try {
                const response = await fetch('/api/sys_logs');
                const data = await response.json();
                const logsContent = document.getElementById('logs-content');
                const logsContainer = document.getElementById('system-logs');
                
                if (logsContent && logsContent.textContent !== data.content) {
                    const atBottom = logsContainer.scrollHeight - logsContainer.scrollTop <= logsContainer.clientHeight + 10;
                    logsContent.textContent = data.content;
                    if (atBottom) {
                        logsContainer.scrollTop = logsContainer.scrollHeight;
                    }
                }
            } catch (e) {
                console.error("Failed to fetch system logs", e);
            }
        }

        // Poll for updates
        setInterval(refreshTasks, 5000);
        setInterval(refreshLogs, 3000);
        setInterval(refreshSystemLogs, 4000);
    </script>
</body>
</html>
"""

def get_sentiment_stats():
    sentiment_file = os.path.join(AGENT_ROOT, "sentiment_log.json")
    stats = {"positive": 0, "negative": 0, "neutral": 0, "total": 0}
    if os.path.exists(sentiment_file):
        try:
            with open(sentiment_file, "r") as f:
                logs = json.load(f)
                stats["total"] = len(logs)
                for entry in logs:
                    s = entry.get("sentiment", "neutral")
                    if s in stats:
                        stats[s] += 1
        except Exception:
            pass
    return stats

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
    
    active_model = "Unknown"
    if os.path.exists(os.path.join(AGENT_ROOT, "active_model.txt")):
        with open(os.path.join(AGENT_ROOT, "active_model.txt"), "r") as f:
            active_model = f.read().strip().split("-")[1].upper() # Simplified name
            
    sentiment = get_sentiment_stats()
    return render_template_string(HTML_TEMPLATE, 
                                tasks=tasks, 
                                pro_usage=pro, 
                                flash_usage=flash, 
                                cpu=cpu, 
                                memory=mem, 
                                chat_entries=chat_entries,
                                active_model=active_model,
                                sentiment=sentiment)

@app.route("/switch_model", methods=["POST"])
def switch_model_route():
    tier = request.form.get("tier")
    model_map = {
        "pro": "gemini-3.1-pro-preview",
        "flash": "gemini-3-flash-preview"
    }
    if tier in model_map:
        with open(os.path.join(AGENT_ROOT, "active_model.txt"), "w") as f:
            f.write(model_map[tier])
        # Signal restart
        with open(os.path.join(AGENT_ROOT, "restart_signal.txt"), "w") as f:
            f.write("model_switch")
    return redirect(url_for("index"))

@app.route("/restart_agent", methods=["POST"])
def restart_agent_route():
    with open(os.path.join(AGENT_ROOT, "restart_signal.txt"), "w") as f:
        f.write("manual_restart")
    return "Restart signal sent. The agent will reboot shortly. <a href='/'>Back to Dashboard</a>"

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

@app.route("/api/logs")
def api_logs():
    return jsonify({"entries": [line.strip() for line in load_chat()]})

@app.route("/api/sys_logs")
def api_sys_logs():
    content = ""
    log_files = ["dashboard_stdout.txt", "dashboard_stderr.txt", "discord_bot_stdout.txt", "discord_bot_stderr.txt", "dev_log.txt"]
    for log in log_files:
        if os.path.exists(log):
            try:
                with open(log, "r") as f:
                    content += f"--- {log} ---\n"
                    lines = f.readlines()
                    content += "".join(lines[-25:]) + "\n\n"
            except Exception as e:
                content += f"Error reading {log}: {e}\n"
    
    # Add heartbeat/process info
    import time
    heartbeat_file = "heartbeat.txt"
    if os.path.exists(heartbeat_file):
        try:
            with open(heartbeat_file, "r") as f:
                ts = float(f.read().strip())
                diff = time.time() - ts
                content += f"--- SYSTEM HEARTBEAT ---\nLast active: {diff:.1f}s ago\n"
        except Exception:
            pass
            
    return jsonify({"content": content})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "uptime": get_system_stats()[1]})

if __name__ == "__main__":
    # Note: Running on port 5000 inside the container.
    app.run(host="0.0.0.0", port=5000)
