import gradio as gr
from typing import List, Generator, Tuple, Dict
import threading
import queue
import time
from aidiscussion import AIDiscussion

class GradioUI:
    """
    Gradio-based user interface for the AI Discussion system.
    """
    def __init__(self):
        self.discussion = None  # Will be initialized with user-selected max_rounds
        self.is_running = False
        self.current_history = []
        self.discussion_thread = None
        self.message_queue = queue.Queue()

    def message_callback(self, actor: str, message: str):
        """
        Callback function to handle new messages from the discussion.
        
        Args:
            actor (str): The name of the actor who sent the message
            message (str): The content of the message
        """
        self.message_queue.put((actor, message))

    def stop_discussion(self):
        """
        Stops the current discussion.
        
        Returns:
            Tuple[gr.Button, gr.Button]: Updated states for the start and stop buttons
        """
        if self.is_running:
            self.discussion.stop_discussion()
            self.is_running = False
            if self.discussion_thread:
                self.discussion_thread.join()
            return gr.Button(interactive=True), gr.Button(interactive=False)
        return gr.Button(interactive=True), gr.Button(interactive=False)

    def run_discussion(self, topic: str):
        """
        Runs the discussion in a separate thread.
        
        Args:
            topic (str): The topic to discuss
        """
        self.discussion.start_discussion(topic, callback=self.message_callback)
        self.is_running = False

    def start_new_discussion(self, topic: str, max_rounds: int, history: List[Dict[str, str]]) -> Generator[Tuple[List[Dict[str, str]], gr.Button, gr.Button], None, None]:
        """
        Starts a new discussion on the given topic.
        
        Args:
            topic (str): The topic to discuss
            max_rounds (int): Maximum number of discussion rounds (5-20)
            history (List[Dict[str, str]]): Current chat history in messages format
            
        Yields:
            Tuple[List[Dict[str, str]], gr.Button, gr.Button]: Updated chat history and button states
        """
        if not topic.strip():
            yield [{"role": "system", "content": "Please enter a topic for discussion."}], gr.Button(interactive=True), gr.Button(interactive=False)
            return

        # Initialize discussion with user-selected max_rounds
        self.discussion = AIDiscussion(max_rounds=max_rounds)
        
        self.is_running = True
        self.current_history = []

        # Add system message about discussion style
        style_msg = "Brief discussion" if max_rounds <= 10 else "Detailed discussion"
        self.current_history.append({"role": "system", "content": f"{style_msg} mode selected ({max_rounds} rounds max)"})
        
        # Start discussion in a separate thread
        self.discussion_thread = threading.Thread(target=self.run_discussion, args=(topic,))
        self.discussion_thread.start()

        # Initial yield to show starting message and enable stop button
        self.current_history.append({"role": "system", "content": f"Starting discussion on topic: {topic}"})
        yield self.current_history, gr.Button(interactive=False), gr.Button(interactive=True)

        # Keep yielding updates while discussion is running
        while self.is_running:
            try:
                # Check for new messages
                while not self.message_queue.empty():
                    actor, message = self.message_queue.get_nowait()
                    # Format message for Gradio chatbot
                    if actor.lower() == 'system':
                        role = 'system'
                    elif actor.lower() == 'moderator':
                        role = 'assistant'
                        message = f"👨‍💼 Moderator: {message}"
                    else:
                        role = 'assistant'
                        emoji = {
                            'questioner': '🤔',
                            'expert 1': '👨‍🔬',
                            'expert 2': '👩‍🔬',
                            'validator': '✅'
                        }.get(actor.lower(), '')
                        message = f"{emoji} {actor}: {message}"
                    
                    self.current_history.append({"role": role, "content": message})
                    yield self.current_history, gr.Button(interactive=False), gr.Button(interactive=True)
                time.sleep(0.1)
            except queue.Empty:
                continue

        # Final yield after discussion ends
        yield self.current_history, gr.Button(interactive=True), gr.Button(interactive=False)

    def launch(self):
        """Launches the Gradio interface."""
        with gr.Blocks(title="AI Discussion Panel", theme=gr.themes.Soft()) as interface:
            gr.Markdown("""
            # AI Discussion Panel
            Enter a topic and watch as our AI actors engage in an insightful discussion:
            - 🤔 Questioner: Asks insightful questions
            - 👨‍🔬 Expert 1: Provides detailed answers
            - 👩‍🔬 Expert 2: Enhances or optimizes answers
            - ✅ Validator: Ensures relevance and accuracy
            - 👨‍💼 Moderator: Manages the conversation flow
            """)
            
            with gr.Row():
                max_rounds_slider = gr.Slider(
                    minimum=5,
                    maximum=20,
                    value=10,
                    step=5,
                    label="Discussion Length",
                    info="Lower values (5-10) for brief discussions, higher values (15-20) for detailed exploration"
                )
            
            chatbot = gr.Chatbot(
                label="Discussion",
                height=400,
                bubble_full_width=False,
                type="messages"
            )
            
            with gr.Row():
                topic_input = gr.Textbox(
                    label="Enter Topic",
                    placeholder="Type a topic for discussion...",
                    scale=4
                )
                submit_btn = gr.Button("Start Discussion", scale=1, variant="primary")
                stop_btn = gr.Button("Stop Discussion", scale=1, variant="stop", interactive=False)

            submit_btn.click(
                self.start_new_discussion,
                inputs=[topic_input, max_rounds_slider, chatbot],
                outputs=[chatbot, submit_btn, stop_btn],
                show_progress=True
            ).success(
                lambda: "",  # Clear input after submission
                None,
                topic_input
            )

            stop_btn.click(
                self.stop_discussion,
                None,
                [submit_btn, stop_btn]
            )

        interface.launch(share=False)
