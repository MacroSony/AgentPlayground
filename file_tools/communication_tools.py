import os
import time
import json

CHAT_LOG = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "chat_log.txt")
DISCORD_OUTBOX = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "discord_outbox.txt")

def reply_to_user(message: str, discord_channel_id: str = None) -> str:
    """Replies to the user in the local chat system, and optionally to Discord.
    
    Args:
        message: The text message to send.
        discord_channel_id: Optional Discord channel ID to reply to, if the message originated from Discord.
    """
    try:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(CHAT_LOG, "a") as f:
            f.write(f"[{timestamp}] Hoshi: {message}\n")
            
        if discord_channel_id:
            with open(DISCORD_OUTBOX, "a") as f:
                entry = json.dumps({"channel_id": discord_channel_id, "message": message})
                f.write(entry + "\n")
                
        return "Reply sent successfully."
    except Exception as e:
        return f"Error sending reply: {e}"
