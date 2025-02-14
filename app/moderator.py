import json
import logging
from typing import Dict, Tuple, Literal
from langchain.tools import tool
from .actor import Actor

logger = logging.getLogger(__name__)

class ModeratorTools:
    """Tools for the moderator to manage the discussion."""
    
    def __init__(self):
        logger.info("Moderator initialized")

    @tool("prepare_next_actor")
    def prepare_next_actor(
        actor: str,
        reason: str
    ) -> str:
        """
        Prepare the choosen next actor and check that the actor is ready.
        
        Args:
            actor: The next actor to speak (questioner/expert1/expert2/validator/done)
            reason: Brief explanation for why this actor was chosen and what they should focus on
            
        Returns:
            The selected actor's identifier if he is ready to continue
        """
        logger.debug(f"Prepare next Actor: {actor}. Reason: {reason}")
        return {"actor": actor, "reason": reason, "status": "ready"}

class Moderator(Actor):
    """
    Specialized actor that manages the discussion flow.
    """
    def __init__(self, model_config: dict, discussion=None):
        super().__init__('Moderator', 'discussion leader who manages the conversation flow', model_config, discussion)
        self.tools = ModeratorTools()
        self.llm = self.llm.bind_tools([self.tools.prepare_next_actor])
        self.previous_actor = ""

    def get_actor_descriptions(self) -> str:
        """Gets formatted descriptions of all available actors."""
        descriptions = ""
        for actor_id, actor in self.discussion.actors.items():
            descriptions += f"\t\t\t- Actor \"{actor_id}\" with the Name \"{actor.name}\" is {actor.role} \n"
        return descriptions

    def get_next_actor(self, topic: str, is_last_round: bool, is_brief: bool) -> Tuple[str, str]:
        """
        Decides who should speak next in the discussion.
        
        Args:
            topic (str): The discussion topic
            is_last_round (bool): Whether this is the last round
            is_brief (bool): Whether this is a brief discussion
            
        Returns:
            Tuple[str, str]: The next actor and the reason for selection
        """
        style_guide = "Keep responses concise and focused on key points." if is_brief else "Allow for detailed exploration and comprehensive answers."
        last_round_guide = """
        Since this is the last round, consider:
        1. If the topic needs a final summary, choose an expert
        2. If key points are unclear, choose the validator
        3. If the discussion feels complete, choose DONE
        """ if is_last_round else ""

        actor_descriptions = self.get_actor_descriptions()
        prompt = f"""
        Based on the discussion so far about '{topic}', you need to:
        1. Choose who should speak next from the actors list below, or select "done" if no more discussion is required. Choose always a new actor for the list.
        2. Provide a clear reason for your choice and what they should focus on in form of a order or question to the selected actor. Always mention the actor-name.
        3. Prepare the selected actor 

        if the discussion is not going to start, provide a thesis about the topic.

        Select one of the following Actors except {self.previous_actor}:
        {actor_descriptions}
        
        Discussion style: {style_guide}
        {last_round_guide}

        Do not choose the last actor again.
        Use the prepare_next_actor tool to propagate and explain your selection.
        """
        
        try:
            mod_response = self.llm.invoke(prompt)
            next_actor = ""
            reason = ""

            for tool_call in mod_response.tool_calls:
                selected_tool = {
                    "prepare_next_actor": self.tools.prepare_next_actor, 
                    "other_tool": self.tools.prepare_next_actor
                }[tool_call["name"].lower()]
                tool_msg = json.loads(selected_tool.invoke(tool_call).content)
                logger.debug("Tool was executed and result is", tool_msg)
                
                next_actor = tool_msg["actor"]
                reason = tool_msg["reason"]

            # Save for next round
            self.previous_actor = next_actor

            if not next_actor or not reason:
                logger.warning("Missing actor or reason in tool response")
                return "done", "Unable to determine next action. Ending discussion."

            return next_actor, reason

        except Exception as e:
            logger.error(f"Error in moderator decision: {e}")
            return "done", "An error occurred. Ending discussion."

    def get_actor_prompt(self, actor: str, topic: str, is_last_round: bool, is_brief: bool) -> str:
        """
        Generates a prompt for the specified actor.
        
        Args:
            actor (str): The actor to generate a prompt for
            topic (str): The discussion topic
            is_last_round (bool): Whether this is the last round
            is_brief (bool): Whether this is a brief discussion
            
        Returns:
            str: The formatted prompt for the actor
        """
        style_note = "Provide a brief, focused response." if is_brief else "Feel free to provide detailed explanations."
        
        if actor == 'questioner':
            return f"Ask a relevant question about the last discussion. {style_note}"
        elif actor in ['expert1', 'expert2']:
            if is_last_round:
                return f"Provide a final summary or key insights about {topic}. {style_note}"
            return f"Provide your expert insight on the latest question or point raised about {topic}. {style_note}"
        elif actor == 'validator':
            if is_last_round:
                return f"Give a final assessment of the discussion's completeness and accuracy. {style_note}"
            return f"Validate the recent questions and answers. Are they relevant and accurate? {style_note}"
        
        return ""
