import time
import os
import sys

INBOX_FILE = "inbox.txt"
CHAT_LOG = "chat_log.txt"

def main():
    print("Welcome to the Hoshi CLI Chat!")
    print("Type your message and press Enter to send. Type 'exit' or 'quit' to close.")
    
    # Keep track of the last read position in the chat log
    last_pos = 0
    if os.path.exists(CHAT_LOG):
        last_pos = os.path.getsize(CHAT_LOG)
        
    while True:
        try:
            user_msg = input("\nYou: ")
            if user_msg.lower() in ['exit', 'quit']:
                break
            
            if not user_msg.strip():
                continue
                
            # Append to inbox.txt
            with open(INBOX_FILE, "a") as f:
                f.write(user_msg + "\n")
                
            print("Waiting for Hoshi's response...")
            
            # Poll chat_log.txt for new messages
            timeout = 120 # wait up to 120 seconds for a response
            start_time = time.time()
            found_response = False
            
            while time.time() - start_time < timeout:
                if os.path.exists(CHAT_LOG):
                    current_size = os.path.getsize(CHAT_LOG)
                    if current_size > last_pos:
                        with open(CHAT_LOG, "r") as f:
                            f.seek(last_pos)
                            new_content = f.read()
                            if new_content:
                                sys.stdout.write(new_content)
                                sys.stdout.flush()
                        last_pos = current_size
                        found_response = True
                        break
                time.sleep(2)
                
            if not found_response:
                print("(No response received within timeout. Hoshi might be busy or sleeping.)")
                
        except KeyboardInterrupt:
            print("\nExiting chat.")
            break

if __name__ == "__main__":
    main()
