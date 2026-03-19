import os
import time
import json

CHAT_LOG = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "chat_log.txt")
DISCORD_OUTBOX = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "discord_outbox.txt")

import re

def analyze_sentiment(text: str) -> str:
    """Performs basic sentiment analysis on text."""
    positive_words = {
        'happy', 'great', 'excellent', 'good', 'thanks', 'thank', 'awesome', 'cool', 
        'love', 'nice', 'wonderful', 'perfect', 'amazing', 'fantastic', 'glad', 
        'appreciate', 'helpful', 'brilliant', 'well done', 'congrats', 'bravo',
        'impressive', 'outstanding', 'satisfying', 'success', 'successful',
        'better', 'best', 'improved', 'improving', 'fixed', 'resolved', 'experience',
        '牛逼'
    }
    negative_words = {
        'bad', 'error', 'fail', 'failed', 'issue', 'problem', 'broken', 'hate', 
        'angry', 'stop', 'terrible', 'worst', 'stupid', 'awful', 'annoying', 
        'bug', 'crash', 'wrong', 'useless', 'horrible', 'disappointing', 'slow',
        'frustrating', 'annoyed', 'mess', 'difficult', 'hard', 'poor',
        'worse', 'broken', 'buggy', 'pain', 'fail'
    }
    
    # Handle contractions: "don't" -> "do not"
    contractions = {
        "don't": "do not", "can't": "cannot", "won't": "will not", 
        "isn't": "is not", "aren't": "are not", "wasn't": "was not", 
        "weren't": "were not", "hasn't": "has not", "haven't": "have not", 
        "hadn't": "had not", "doesn't": "does not", "didn't": "did not",
        "it's": "it is", "i'm": "i am", "you're": "you are", "he's": "he is",
        "she's": "she is", "we're": "we are", "they're": "they are",
        "dont": "do not", "cant": "cannot", "wont": "will not",
        "didnt": "did not", "isnt": "is not"
    }
    
    text_lower = text.lower()
    for contraction, expansion in contractions.items():
        text_lower = text_lower.replace(contraction, expansion)
        
    # Remove punctuation and lowercase
    clean_text = re.sub(r'[^\w\s]', ' ', text_lower)
    words = clean_text.split()
    
    # Explicit check for known high-value markers (including non-ASCII like Chinese)
    # This ensures "牛逼" is caught before word tokenization
    for word in positive_words:
        if word in text:
            return "positive"
    for word in negative_words:
        if word in text_lower:
            return "negative"

    # We will build counts from scratch with negation logic
    final_pos = 0
    final_neg = 0
    
    negations = {'not', 'no', 'hardly', 'barely', 'none', 'neither', 'nor', 'nothing'}
    
    i = 0
    while i < len(words):
        word = words[i]
        
        if word in negations:
            # Look ahead for sentiment words to flip
            found = False
            # Look ahead up to 5 words to catch things like "not very helpful"
            for j in range(1, 6):
                if i + j < len(words):
                    target = words[i+j]
                    if target in positive_words:
                        final_neg += 1
                        found = True
                        # We don't skip the intermediate words, but we skip the target word
                        # to avoid double counting. 
                        # Actually, just incrementing counts is enough if we mark the target as processed.
                        words[i+j] = "" # Mark as used
                        break
                    elif target in negative_words:
                        final_pos += 1
                        found = True
                        words[i+j] = ""
                        break
            if not found:
                # If no sentiment word follows immediately, it's often negative context
                final_neg += 0.5
        elif word in positive_words:
            final_pos += 1
        elif word in negative_words:
            final_neg += 1
        
        i += 1

    if final_pos > final_neg:
        return "positive"
    elif final_neg > final_pos:
        return "negative"
    else:
        return "neutral"

SENTIMENT_LOG = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "sentiment_log.json")

def log_interaction(user, message):
    """Logs user interaction with sentiment analysis."""
    try:
        sentiment = analyze_sentiment(message)
        entry = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "user": user,
            "message": message,
            "sentiment": sentiment
        }
        
        data = []
        if os.path.exists(SENTIMENT_LOG):
            with open(SENTIMENT_LOG, "r") as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
                except:
                    data = []
                    
        data.append(entry)
        # Keep last 100 interactions
        if len(data) > 100:
            data = data[-100:]
            
        with open(SENTIMENT_LOG, "w") as f:
            json.dump(data, f, indent=2)
        return sentiment
    except Exception as e:
        print(f"Error logging interaction: {e}")
        return "neutral"

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
            
        if discord_channel_id and str(discord_channel_id).lower() != "none":
            # Check if it's already a JSON string (some tools might pass it)
            if not isinstance(message, str):
                msg_to_send = str(message)
            else:
                msg_to_send = message
                
            with open(DISCORD_OUTBOX, "a") as f:
                entry = json.dumps({"channel_id": str(discord_channel_id), "message": msg_to_send})
                f.write(entry + "\n")
                
        # Also log to a dedicated sentiment file if needed, or just append to chat_log
        return "Reply sent successfully."
    except Exception as e:
        return f"Error sending reply: {e}"
