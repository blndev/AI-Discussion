from main import AIDiscussion
import threading
import select
import sys
import time
import os

class ConsoleUI:
    def __init__(self):
        self.discussion = AIDiscussion()
        self.is_running = False

    def message_callback(self, actor: str, message: str):
        print(f"\n{actor}: {message}")

    def stop_discussion(self):
        if self.is_running:
            self.discussion.stop_discussion()
            self.is_running = False
            print("\nStopping discussion...")

    def check_input(self, timeout=0.1):
        """Check for input with timeout, returns True if 'q' was pressed"""
        if os.name == 'nt':  # Windows
            import msvcrt
            if msvcrt.kbhit():
                if msvcrt.getch() == b'q':
                    return True
        else:  # Unix-like
            i, _, _ = select.select([sys.stdin], [], [], timeout)
            if i and sys.stdin.readline().strip() == 'q':
                return True
        return False

    def run(self):
        print("Welcome to AI Discussion Panel (Console Version)!")
        print("\nAt any time during a discussion:")
        if os.name == 'nt':  # Windows
            print("- Press 'q' to stop the current discussion")
        else:  # Unix-like
            print("- Type 'q' and press Enter to stop the current discussion")

        while True:
            topic = input("\nEnter a topic for discussion (or 'quit' to exit): ")
            if topic.lower() == 'quit':
                break
            
            print("\nStarting discussion...\n")
            self.is_running = True
            
            # Start discussion in a separate thread
            discussion_thread = threading.Thread(
                target=self.discussion.start_discussion,
                args=(topic, self.message_callback)
            )
            discussion_thread.daemon = True
            discussion_thread.start()

            # Wait for 'q' input or discussion to finish
            while discussion_thread.is_alive():
                if self.check_input():
                    self.stop_discussion()
                    break
                time.sleep(0.1)
            
            discussion_thread.join()
            self.is_running = False
            print("\nDiscussion finished!")

if __name__ == "__main__":
    console = ConsoleUI()
    console.run()
