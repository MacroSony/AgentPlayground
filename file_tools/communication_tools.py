import os
import time

CHAT_LOG = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "chat_log.txt")

def reply_to_user(message: str) -> str:
    """Replies to the user in the local chat system.
    
    Args:
        message: The text message to send to the user.
    """
    try:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(CHAT_LOG, "a") as f:
            f.write(f"[{timestamp}] Hoshi: {message}\n")
        return "Reply sent successfully."
    except Exception as e:
        return f"Error sending reply: {e}"
