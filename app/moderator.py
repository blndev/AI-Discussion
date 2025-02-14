import json
import logging
import random
from typing import Dict, Tuple, Literal
from .actor import Actor

logger = logging.getLogger(__name__)

class Moderator(Actor):
    """
    Specialized actor that manages the discussion flow.
    """
    def __init__(self, model_config: dict, discussion=None):
        super().__init__('Moderator', 'discussion leader who manages the conversation flow', model_config, discussion)
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
            Tuple[str, str]: The next actor ID and the reason/prompt for that actor
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
        2. Provide a clear reason for your choice and what they should focus on.

        Select one of the following Actors except {self.previous_actor}:
        {actor_descriptions}
        
        Discussion style: {style_guide}
        {last_round_guide}

        Do not choose the last actor again.
        Respond in JSON format with two fields:
        {{
            "actor": "selected_actor_id",
            "reason": "explanation for choice and focus"
        }}
        """
        
        try:
            response = self.llm.invoke(prompt)
            
            try:
                result = json.loads(response.content)
                next_actor = result.get("actor", "")
                reason = result.get("reason", "")

                if not next_actor or not reason:
                    raise ValueError("Missing actor or reason in response")
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse LLM response: {e}")
                # Get available actors excluding previous actor and 'done'
                available_actors = [
                    actor_id for actor_id in self.discussion.actors.keys() 
                    if actor_id != self.previous_actor and actor_id != "done"
                ]
                if not available_actors:
                    return "done", "No available actors. Ending discussion."
                
                # Randomly select an actor as fallback
                next_actor = random.choice(available_actors)
                reason = f"Fallback selection due to response parsing error. Continuing discussion with {next_actor}."

            # Save for next round
            self.previous_actor = next_actor
            return next_actor, reason

        except Exception as e:
            logger.error(f"Error in moderator decision: {e}")
            return "done", "An error occurred. Ending discussion."
