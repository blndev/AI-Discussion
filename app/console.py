import threading
import select
import sys
import time
import os
from .discussion import AIDiscussion
from .app import App

class ConsoleUI(App):
    """Console-based user interface for the AI Discussion system."""
    
    def __init__(self, model_config: dict):
        """
        Initialize the console UI.
        
        Args:
            model_config (dict): Configuration for the LLM model
        """
        super().__init__(model_config)
        self.discussion = AIDiscussion(model_config=model_config)
        self.is_running = False

    def message_callback(self, actor: str, message: str):
        """
        Callback function to handle new messages from the discussion.
        
        Args:
            actor (str): The name of the actor who sent the message
            message (str): The content of the message
        """
        print(f"\n{actor}: {message}")

    def stop_discussion(self):
        """Stops the current discussion."""
        if self.is_running:
            self.discussion.stop_discussion()
            self.is_running = False
            print("\nStopping discussion...")

    def check_input(self, timeout=0.1):
        """
        Check for input with timeout.
        
        Args:
            timeout (float): Time to wait for input
            
        Returns:
            bool: True if 'q' was pressed
        """
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

    def launch(self):
        """Runs the console interface."""
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
