from langchain_ollama import ChatOllama
from typing import List, Dict

class Actor:
    """
    Represents an AI actor in the discussion.
    
    Args:
        name (str): The name of the actor
        role (str): The role description of the actor
        model_config (dict): Configuration for the LLM model
        discussion: The discussion this actor is part of
    """
    def __init__(self, name: str, role: str, model_config: dict, discussion=None):
        self.name = name
        self.role = role
        self.discussion = discussion
        self.llm = ChatOllama(
            model=model_config["model"],
            temperature=model_config["model_params"]["temperature"],
            top_p=model_config["model_params"]["top_p"]
        )

    def get_context(self) -> List[Dict]:
        """Gets the current discussion context from the discussion history."""
        return self.discussion.discussion_history[-5:] if self.discussion else []

    def get_prompt(self, message: str) -> str:
        """
        Generates a prompt for the actor based on context and current message.
        
        Args:
            message (str): The current message to respond to
            
        Returns:
            str: The formatted prompt including context and role information
        """
        context_str = "\n".join([f"{msg['actor']}: {msg['message']}" for msg in self.get_context()])
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
        return response.content
