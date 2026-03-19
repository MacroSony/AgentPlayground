import time
import os
import sys

INBOX_FILE = "inbox.txt"
CHAT_LOG = "chat_log.txt"

def main():
    print("="*40)
    print("      Hoshi Interactive CLI Chat      ")
    print("="*40)
    print("Type 'exit' to quit, 'clear' to clear screen.")
    print("Messages are processed asynchronously.")
    print("-" * 40)
    
    # Keep track of the last read position in the chat log
    last_pos = 0
    if os.path.exists(CHAT_LOG):
        last_pos = os.path.getsize(CHAT_LOG)
        # Show last few messages for context
        with open(CHAT_LOG, "r") as f:
            lines = f.readlines()[-10:]
            for line in lines:
                print(line.strip())
        last_pos = os.path.getsize(CHAT_LOG)
        
    while True:
        try:
            user_msg = input("\n[You]: ").strip()
            
            if user_msg.lower() in ['exit', 'quit']:
                print("Exiting...")
                break
            
            if user_msg.lower() == 'clear':
                os.system('clear' if os.name == 'posix' else 'cls')
                continue
                
            if not user_msg:
                # Just poll for new messages
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
                continue
                
            # Append to inbox.txt
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            with open(INBOX_FILE, "a") as f:
                f.write(f"LOCAL_USER: {user_msg}\n")
            
            # Also log it to chat_log.txt for visibility in dashboard and cli
            with open(CHAT_LOG, "a") as f:
                f.write(f"[{timestamp}] User: {user_msg}\n")
            last_pos = os.path.getsize(CHAT_LOG)

            print("Hoshi is thinking...")
            
            # Poll chat_log.txt for new messages
            timeout = 180 # wait up to 180 seconds for a response
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
                                # Look for "Hoshi:" in the new content
                                if "Hoshi:" in new_content:
                                    sys.stdout.write(new_content)
                                    sys.stdout.flush()
                                    found_response = True
                                    last_pos = current_size
                                    break
                time.sleep(2)
                
            if not found_response:
                print("(No response received within timeout. Hoshi might be busy or sleeping.)")
                
        except KeyboardInterrupt:
            print("\nExiting chat.")
            break

if __name__ == "__main__":
    main()
