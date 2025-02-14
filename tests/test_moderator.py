import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from app.moderator import Moderator

class TestModerator(unittest.TestCase):
    """Test cases for the Moderator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.model_config = {
            "model": "test-model",
            "model_params": {
                "temperature": 0.7,
                "top_p": 0.8
            }
        }
        # Mock discussion with actors
        self.mock_discussion = Mock()
        self.mock_discussion.actors = {
            'expert1': Mock(name="Expert 1", role="test expert role"),
            'questioner': Mock(name="Questioner", role="test questioner role")
        }
        
    def test_get_next_actor_success(self):
        """Test successful actor selection."""
        with patch('app.actor.ChatOllama') as mock_chat_ollama:
            # Setup mock LLM response
            mock_response = MagicMock()
            mock_response.content = json.dumps({
                "actor": "expert1",
                "reason": "Need expert insight"
            })
            mock_llm = MagicMock()
            mock_llm.invoke = MagicMock(return_value=mock_response)
            mock_chat_ollama.return_value = mock_llm
            
            # Create moderator with mocked LLM
            moderator = Moderator(self.model_config, self.mock_discussion)
            
            next_actor, reason = moderator.get_next_actor(
                topic="test topic",
                is_last_round=False,
                is_brief=True
            )
        
        self.assertEqual(next_actor, "expert1")
        self.assertEqual(reason, "Need expert insight")
        self.assertEqual(moderator.previous_actor, "expert1")

    def test_get_next_actor_handles_non_json_response(self):
        """Test handling of non-JSON LLM response with fallback to random actor."""
        with patch('app.actor.ChatOllama') as mock_chat_ollama:
            # Setup mock LLM with non-JSON response
            mock_response = MagicMock()
            mock_response.content = "Not a JSON response"
            mock_llm = MagicMock()
            mock_llm.invoke = MagicMock(return_value=mock_response)
            mock_chat_ollama.return_value = mock_llm
            
            # Create moderator with mocked LLM
            moderator = Moderator(self.model_config, self.mock_discussion)
            
            next_actor, reason = moderator.get_next_actor(
                topic="test topic",
                is_last_round=False,
                is_brief=True
            )
        
        # Verify that an actor was selected and it's not the previous actor
        self.assertIn(next_actor, ["expert1", "questioner"])
        self.assertIn("Fallback selection", reason)
        self.assertEqual(next_actor, moderator.previous_actor)

    def test_get_next_actor_handles_error(self):
        """Test handling of LLM error."""
        with patch('app.actor.ChatOllama') as mock_chat_ollama:
            # Setup mock LLM that raises an error
            mock_llm = MagicMock()
            mock_llm.invoke = MagicMock(side_effect=Exception("LLM error"))
            mock_chat_ollama.return_value = mock_llm
            
            # Create moderator with mocked LLM
            moderator = Moderator(self.model_config, self.mock_discussion)
            
            next_actor, reason = moderator.get_next_actor(
                topic="test topic",
                is_last_round=False,
                is_brief=True
            )
        
        self.assertEqual(next_actor, "done")
        self.assertIn("An error occurred", reason)

    def test_get_actor_descriptions(self):
        """Test that get_actor_descriptions formats actor info correctly."""
        with patch('app.actor.ChatOllama'):
            moderator = Moderator(self.model_config, self.mock_discussion)
            descriptions = moderator.get_actor_descriptions()
        
        # Verify descriptions contain actor information
        self.assertIn("Expert 1", descriptions)
        self.assertIn("test expert role", descriptions)
        self.assertIn("Questioner", descriptions)
        self.assertIn("test questioner role", descriptions)


if __name__ == '__main__':
    unittest.main()
