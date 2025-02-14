import gradio as gr
from typing import List, Generator, Tuple, Dict
import threading
import queue
import time
import logging
from .discussion import AIDiscussion
from .app import App

logger = logging.getLogger(__name__)

class GradioUI(App):
    """
    Gradio-based user interface for the AI Discussion system.
    """
    def __init__(self, model_config: dict):
        super().__init__(model_config)
        logger.info("Initializing Gradio UI")
        self.model_config = model_config
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
            logger.info("Stopping discussion")
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

    def start_new_discussion(
        self, topic: str, max_rounds: int, history: List[Dict[str, str]],
        custom_enabled: bool = False,
        questioner_enabled: bool = True, questioner_name: str = "Questioner", questioner_role: str = "",
        expert1_enabled: bool = True, expert1_name: str = "Expert 1", expert1_role: str = "",
        expert2_enabled: bool = True, expert2_name: str = "Expert 2", expert2_role: str = "",
        validator_enabled: bool = True, validator_name: str = "Validator", validator_role: str = ""
    ) -> Generator[Tuple[List[Dict[str, str]], gr.Button, gr.Button, bool], None, None]:
        """
        Starts a new discussion on the given topic.
        
        Args:
            topic (str): The topic to discuss
            max_rounds (int): Maximum number of discussion rounds (5-100)
            history (List[Dict[str, str]]): Current chat history in messages format
            
        Yields:
            Tuple[List[Dict[str, str]], gr.Button, gr.Button]: Updated chat history and button states
        """
        if not topic.strip():
            gr.Warning("Please enter a topic for discussion")
            yield [{"role": "system", "content": "Please enter a topic for discussion."}], gr.Button(interactive=True), gr.Button(interactive=False), True
            return

        # Initialize discussion with user-selected configuration
        custom_actors = None
        if custom_enabled:
            custom_actors = {
                'questioner': {
                    'enabled': questioner_enabled,
                    'name': questioner_name,
                    'role': questioner_role
                },
                'expert1': {
                    'enabled': expert1_enabled,
                    'name': expert1_name,
                    'role': expert1_role
                },
                'expert2': {
                    'enabled': expert2_enabled,
                    'name': expert2_name,
                    'role': expert2_role
                },
                'validator': {
                    'enabled': validator_enabled,
                    'name': validator_name,
                    'role': validator_role
                }
            }
        
        self.discussion = AIDiscussion(
            max_rounds=max_rounds,
            model_config=self.model_config,
            custom_actors=custom_actors
        )
        
        self.is_running = True
        self.current_history = []

        # Add system message about discussion style
        style_msg = "Brief discussion" if max_rounds <= 10 else "Detailed discussion"
        self.current_history.append({"role": "system", "content": f"{style_msg} mode selected ({max_rounds} rounds max)"})
        
        # Start discussion in a separate thread
        logger.info("Starting discussion thread")
        self.discussion_thread = threading.Thread(target=self.run_discussion, args=(topic,))
        self.discussion_thread.start()

        # Initial yield to show starting message and enable stop button
        self.current_history.append({"role": "system", "content": f"Starting discussion on topic: {topic}"})
        yield self.current_history, gr.Button(interactive=False), gr.Button(interactive=True), False

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
                    yield self.current_history, gr.Button(interactive=False), gr.Button(interactive=True), False
                time.sleep(0.1)
            except queue.Empty:
                continue

        # Final yield after discussion ends
        yield self.current_history, gr.Button(interactive=True), gr.Button(interactive=False), False

    def launch(self):
        """Launches the Gradio interface."""
        logger.info("Launching Gradio interface")
        with gr.Blocks(title="AI Discussion Panel", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# AI Discussion Panel")
            
            with gr.Tabs() as tabs:
                # Discussion tab (index 0)
                discussion_tab = gr.Tab("Discussion")
                with discussion_tab:
                    gr.Markdown("Enter a topic and press Enter or click Start Discussion to begin an AI-powered conversation.")
                    
                    with gr.Row():
                        max_rounds_slider = gr.Slider(
                            minimum=5,
                            maximum=100,
                            value=20,
                            step=5,
                            label="Discussion Length",
                            info="Adjust the number of discussion rounds (5-100)"
                        )
                    
                    chatbot = gr.Chatbot(
                        label="Discussion",
                        height=400,
                        bubble_full_width=False,
                        type="messages"
                    )
                    
                    with gr.Row():
                        topic_input = gr.Textbox(
                            label="",
                            placeholder="Type a topic for discussion...",
                            scale=4
                        )
                        submit_btn = gr.Button("Start Discussion", scale=1, variant="primary")
                        stop_btn = gr.Button("Stop Discussion", scale=1, variant="stop", interactive=False)

                # Custom Actors tab (index 1)
                actors_tab = gr.Tab("Custom Actors")
                with actors_tab:
                    with gr.Row():
                        custom_actors_enabled = gr.Checkbox(
                            label="Enable Custom Actors",
                            value=False,
                            info="Enable to customize which actors participate in the discussion"
                        )
                    
                    with gr.Column(visible=False) as actor_options:
                        with gr.Row():
                            questioner_enabled = gr.Checkbox(label="Questioner", value=True)
                            questioner_name = gr.Textbox(label="Name", value="Questioner", interactive=True)
                            questioner_role = gr.Textbox(
                                label="Role",
                                value="curious individual who asks insightful questions about the topic",
                                interactive=True,
                                scale=2
                            )
                        
                        with gr.Row():
                            expert1_enabled = gr.Checkbox(label="Expert 1", value=True)
                            expert1_name = gr.Textbox(label="Name", value="Expert 1", interactive=True)
                            expert1_role = gr.Textbox(
                                label="Role",
                                value="knowledgeable expert who provides detailed insights and answers",
                                interactive=True,
                                scale=2
                            )
                        
                        with gr.Row():
                            expert2_enabled = gr.Checkbox(label="Expert 2", value=True)
                            expert2_name = gr.Textbox(label="Name", value="Expert 2", interactive=True)
                            expert2_role = gr.Textbox(
                                label="Role",
                                value="knowledgeable expert who provides detailed insights and answers",
                                interactive=True,
                                scale=2
                            )
                        
                        with gr.Row():
                            validator_enabled = gr.Checkbox(label="Validator", value=True)
                            validator_name = gr.Textbox(label="Name", value="Validator", interactive=True)
                            validator_role = gr.Textbox(
                                label="Role",
                                value="critical thinker who validates questions and answers",
                                interactive=True,
                                scale=2
                            )
                    
                    def update_actors_visibility(enabled: bool):
                        """Update actor options visibility."""
                        return gr.Column(visible=enabled)

                    custom_actors_enabled.change(
                        update_actors_visibility,
                        inputs=[custom_actors_enabled],
                        outputs=[actor_options]
                    ).then(
                        lambda: 0,  # Switch to Discussion tab (index 0)
                        outputs=tabs
                    )

            # Submit on Enter key or button click
            inputs = [
                topic_input, max_rounds_slider, chatbot,
                custom_actors_enabled,
                questioner_enabled, questioner_name, questioner_role,
                expert1_enabled, expert1_name, expert1_role,
                expert2_enabled, expert2_name, expert2_role,
                validator_enabled, validator_name, validator_role
            ]
            outputs = [chatbot, submit_btn, stop_btn, gr.Checkbox(visible=False)]

            topic_input.submit(
                self.start_new_discussion,
                inputs=inputs,
                outputs=outputs,
                show_progress=True
            )

            submit_btn.click(
                self.start_new_discussion,
                inputs=inputs,
                outputs=outputs,
                show_progress=True
            )

            stop_btn.click(
                self.stop_discussion,
                None,
                [submit_btn, stop_btn]
            )

        interface.launch(share=False)
