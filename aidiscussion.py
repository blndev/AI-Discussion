from langchain_ollama import ChatOllama
from typing import List, Dict, Optional, Callable
import time
import re
import logging

logger = logging.getLogger(__name__)

class Actor:
    """
    Represents an AI actor in the discussion.
    
    Args:
        name (str): The name of the actor
        role (str): The role description of the actor
        model_name (str): The name of the Ollama model to use (default: "playground")
    """
    def __init__(self, name: str, role: str, model_name: str = "playground"):
        self.name = name
        self.role = role
        self.llm = ChatOllama(model=model_name)
        self.context = []

    def get_prompt(self, message: str) -> str:
        """
        Generates a prompt for the actor based on context and current message.
        
        Args:
            message (str): The current message to respond to
            
        Returns:
            str: The formatted prompt including context and role information
        """
        context_str = "\n".join([f"{msg['actor']}: {msg['message']}" for msg in self.context[-5:]])
        return f"""You are {self.name}, a {self.role}. 
Previous context:
{context_str}

Current message: {message}

Respond in character as {self.name}, the {self.role}."""

    def respond(self, message: str) -> str:
        """
        Generates a response from the actor based on the input message.
        
        Args:
            message (str): The message to respond to
            
        Returns:
            str: The actor's response
        """
        prompt = self.get_prompt(message)
        response = self.llm.invoke(prompt)
        self.context.append({"actor": self.role, "message": response.content})
        return response.content

class AIDiscussion:
    """
    Manages an AI-driven discussion between multiple actors.
    """
    def __init__(self, max_rounds: int = 10):
        logger.info(f"Initializing AI Discussion with max_rounds={max_rounds}")
        """
        Initialize the AI Discussion.
        
        Args:
            max_rounds (int): Maximum number of discussion rounds. Lower values (5-10) 
                            result in concise discussions, while higher values (15-20) 
                            allow for more detailed exploration.
        """
        self.stop_flag = False
        self.actors = {
            'questioner': Actor('Questioner', 'curious individual who asks insightful questions about the topic'),
            'expert1': Actor('Expert 1', 'knowledgeable expert who provides detailed answers'),
            'expert2': Actor('Expert 2', 'expert who enhances or optimizes Expert 1\'s answers'),
            'validator': Actor('Validator', 'critical thinker who validates questions and answers'),
            'moderator': Actor('Moderator', 'discussion leader who manages the conversation flow')
        }
        self.discussion_history = []
        self.max_rounds = max_rounds

    def add_to_history(self, actor: str, message: str):
        """
        Adds a message to the discussion history.
        
        Args:
            actor (str): The name of the actor who sent the message
            message (str): The content of the message
        """
        entry = {
            'actor': actor,
            'message': message,
            'timestamp': time.strftime('%H:%M:%S')
        }
        self.discussion_history.append(entry)
        # Update context for all actors
        for actor in self.actors.values():
            actor.context = self.discussion_history

    def extract_next_actor(self, mod_decision: str) -> Optional[str]:
        """
        Extracts the next actor from the moderator's decision.
        
        Args:
            mod_decision (str): The moderator's decision text
            
        Returns:
            Optional[str]: The name of the next actor or None if not found
        """
        # First try to find a direct NEXT: statement
        next_match = re.search(r'NEXT:\s*(questioner|expert1|expert2|validator|DONE)', mod_decision, re.IGNORECASE)
        if next_match:
            return next_match.group(1).lower()

        # If no NEXT: statement, look for any actor mention
        for actor in ['questioner', 'expert1', 'expert2', 'validator']:
            if actor in mod_decision.lower():
                return actor
        
        return None
    
    def stop_discussion(self):
        """Stops the current discussion."""
        self.stop_flag = True
        logger.info("Discussion stopped by user")

    def start_discussion(self, topic: str, callback: Callable[[str, str], None] = None) -> None:
        """
        Starts an AI discussion on the given topic.
        
        Args:
            topic (str): The topic to discuss
            callback (Callable[[str, str], None], optional): Callback function that receives (actor_name, message) updates
        """
        self.stop_flag = False
        self.discussion_history = []
        
        logger.info(f"Starting new discussion on topic: '{topic}' (max_rounds={self.max_rounds})")
        start_msg = f"Starting discussion on topic: {topic}"
        self.add_to_history('system', start_msg)
        if callback:
            callback('System', start_msg)

        rounds = 0
        while rounds < self.max_rounds and not self.stop_flag:
            rounds += 1
            logger.info(f"Starting round {rounds}/{self.max_rounds}")

            # Determine if this is the last round
            is_last_round = rounds == self.max_rounds - 1
            is_brief = self.max_rounds <= 10

            # Moderator decides next action
            style_guide = "Keep responses concise and focused on key points." if is_brief else "Allow for detailed exploration and comprehensive answers."
            last_round_guide = """
            Since this is the last round, consider:
            1. If the topic needs a final summary, choose an expert
            2. If key points are unclear, choose the validator
            3. If the discussion feels complete, choose DONE
            """ if is_last_round else ""

            mod_prompt = f"""Based on the discussion so far about '{topic}', decide who should speak next.
            Discussion style: {style_guide}
            {last_round_guide}
            Your response must start with one of these:
            NEXT: questioner
            NEXT: expert1
            NEXT: expert2
            NEXT: validator
            NEXT: DONE

            Do not choose the last speaker again.
            After stating who should speak next, briefly explain why in one sentence.
            Example: "NEXT: questioner
            We need more specific questions about the topic."
            """
            mod_decision = self.actors['moderator'].respond(mod_prompt)
            if callback:
                callback('Moderator', mod_decision)
            
            next_actor = self.extract_next_actor(str(mod_decision))
            if next_actor == "done" or not next_actor:
                logger.info("Moderator decided to end discussion")
                if callback:
                    callback('Moderator', "Discussion complete. Topic has been thoroughly covered.")
                break

            logger.info(f"Moderator selected next actor: {next_actor}")

            # Get response from the chosen actor
            style_note = "Provide a brief, focused response." if is_brief else "Feel free to provide detailed explanations."
            if next_actor == 'questioner':
                prompt = f"Ask a relevant question about: {topic}. {style_note}"
            elif next_actor in ['expert1', 'expert2']:
                if is_last_round:
                    prompt = f"Provide a final summary or key insights about {topic}. {style_note}"
                else:
                    prompt = f"Provide your expert insight on the latest question or point raised about {topic}. {style_note}"
            elif next_actor == 'validator':
                if is_last_round:
                    prompt = f"Give a final assessment of the discussion's completeness and accuracy. {style_note}"
                else:
                    prompt = f"Validate the recent questions and answers about {topic}. Are they relevant and accurate? {style_note}"
            
            response = self.actors[next_actor].respond(prompt)
            logger.debug(f"Got response from {next_actor} ({len(response)} chars)")
            if callback:
                callback(self.actors[next_actor].name, response)
            self.add_to_history(next_actor, response)
