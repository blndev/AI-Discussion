import gradio as gr
from typing import List, Generator, Tuple, Dict
import threading
import queue
import time
import logging
import json
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
        custom_enabled: bool = False, actors: List[Dict[str, any]] = None
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
        if custom_enabled and actors:
            custom_actors = {f"actor_{i}": actor for i, actor in enumerate(actors)}
        
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
                        with gr.Column(scale=3):
                            custom_actors_enabled = gr.Checkbox(
                                label="Enable Custom Actors",
                                value=False,
                                info="Enable to customize which actors participate in the discussion"
                            )
                        with gr.Column(scale=2):
                            with gr.Row():
                                config_file = gr.Textbox(
                                    label="Config Filename",
                                    value="actor_config.json",
                                    scale=2,
                                    info="Specify the filename to save/load (will be stored in config/ directory)"
                                )
                                save_btn = gr.Button("💾 Save", scale=1)
                                load_btn = gr.Button("📂 Load", scale=1)
                    
                    with gr.Column(visible=False) as actor_options:
                        # Store actors data in State
                        actors_state = gr.State([
                            {
                                "enabled": True,
                                "name": "Questioner",
                                "role": "curious individual who asks insightful questions about the topic"
                            },
                            {
                                "enabled": True,
                                "name": "Expert 1",
                                "role": "knowledgeable expert who provides detailed insights and answers"
                            },
                            {
                                "enabled": True,
                                "name": "Expert 2",
                                "role": "knowledgeable expert who provides detailed insights and answers"
                            },
                            {
                                "enabled": True,
                                "name": "Validator",
                                "role": "critical thinker who validates questions and answers"
                            }
                        ])

                        # Container for actor components
                        with gr.Column() as actors_container:
                            actors_json = gr.TextArea(
                                label="Actor Configuration (JSON)",
                                value="""[
    {
        "enabled": true,
        "name": "Questioner",
        "role": "curious individual who asks insightful questions about the topic"
    },
    {
        "enabled": true,
        "name": "Expert 1",
        "role": "knowledgeable expert who provides detailed insights and answers"
    },
    {
        "enabled": true,
        "name": "Expert 2",
        "role": "knowledgeable expert who provides detailed insights and answers"
    },
    {
        "enabled": true,
        "name": "Validator",
        "role": "critical thinker who validates questions and answers"
    }
]""",
                                lines=20
                            )
                            
                            with gr.Row():
                                apply_btn = gr.Button("Apply Changes", variant="primary")
                                format_btn = gr.Button("Format JSON")

                            def format_json(text):
                                """Format JSON text for better readability."""
                                try:
                                    data = json.loads(text)
                                    return json.dumps(data, indent=4)
                                except:
                                    return text

                            def apply_changes(text):
                                """Apply JSON changes to actors state."""
                                try:
                                    actors = json.loads(text)
                                    # Validate actor structure
                                    for actor in actors:
                                        if not all(k in actor for k in ["enabled", "name", "role"]):
                                            raise ValueError("Each actor must have 'enabled', 'name', and 'role' fields")
                                    return actors, gr.Info("Changes applied successfully")
                                except json.JSONDecodeError as e:
                                    return None, gr.Error(f"Invalid JSON: {str(e)}")
                                except ValueError as e:
                                    return None, gr.Error(str(e))
                                except Exception as e:
                                    return None, gr.Error(f"Error: {str(e)}")

                            format_btn.click(
                                format_json,
                                inputs=[actors_json],
                                outputs=[actors_json]
                            )

                            apply_btn.click(
                                apply_changes,
                                inputs=[actors_json],
                                outputs=[actors_state, actors_json]
                            )
                    
                    def update_actors_visibility(enabled: bool):
                        """Update actor options visibility."""
                        return gr.Column(visible=enabled)
                        
                    def save_config(filename, actors_data):
                        """Save the current actor configuration."""
                        if actors_data is None:
                            return gr.Error("No valid actor configuration to save")
                        try:
                            # Convert list to dictionary format
                            config = {f"actor_{i}": actor for i, actor in enumerate(actors_data)}
                            filepath = f"config/{filename}"
                            AIDiscussion.save_actor_config(config, filepath)
                            return gr.Info("Configuration saved successfully")
                        except Exception as e:
                            return gr.Error(f"Failed to save configuration: {str(e)}")
                            
                    def load_config(filename):
                        """Load actor configuration from file."""
                        try:
                            filepath = f"config/{filename}"
                            config = AIDiscussion.load_actor_config(filepath)
                            # Convert dictionary back to list
                            actors = [actor for _, actor in sorted(config.items())]
                            # Validate actor structure
                            for actor in actors:
                                if not all(k in actor for k in ["enabled", "name", "role"]):
                                    raise ValueError("Invalid configuration: Each actor must have 'enabled', 'name', and 'role' fields")
                            return [
                                actors,
                                json.dumps(actors, indent=4),
                                gr.Info("Configuration loaded successfully")
                            ]
                        except FileNotFoundError:
                            return [
                                actors_state.value,  # Keep current state
                                json.dumps(actors_state.value, indent=4),
                                gr.Error(f"Configuration file not found: {filename}")
                            ]
                        except json.JSONDecodeError as e:
                            return [
                                actors_state.value,  # Keep current state
                                json.dumps(actors_state.value, indent=4),
                                gr.Error(f"Invalid JSON in configuration file: {str(e)}")
                            ]
                        except Exception as e:
                            return [
                                actors_state.value,  # Keep current state
                                json.dumps(actors_state.value, indent=4),
                                gr.Error(f"Failed to load configuration: {str(e)}")
                            ]

                    custom_actors_enabled.change(
                        update_actors_visibility,
                        inputs=[custom_actors_enabled],
                        outputs=[actor_options]
                    ).then(
                        lambda: 0,  # Switch to Discussion tab (index 0)
                        outputs=tabs
                    )
                    
                    # Save button click handler
                    save_btn.click(
                        save_config,
                        inputs=[config_file, actors_state],
                        outputs=[gr.Text(visible=False)]  # For notifications
                    )
                    
                    # Load button click handler
                    load_btn.click(
                        load_config,
                        inputs=[config_file],
                        outputs=[actors_state, actors_json, gr.Text(visible=False)]  # For notifications
                    )

                    # Update JSON when tab is selected
                    def on_tab_select(actors):
                        """Update JSON when tab is selected."""
                        if actors is None:
                            actors = json.loads(actors_json.value)
                        return json.dumps(actors, indent=4)

                    actors_tab.select(
                        on_tab_select,
                        inputs=[actors_state],
                        outputs=[actors_json]
                    )


            # Submit on Enter key or button click
            inputs = [
                topic_input, max_rounds_slider, chatbot,
                custom_actors_enabled, actors_state
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
