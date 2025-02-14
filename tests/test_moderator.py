import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from app.moderator import Moderator, ModeratorTools

class TestModeratorTools(unittest.TestCase):
    """Test cases for the ModeratorTools class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tools = ModeratorTools()

    def test_prepare_next_actor_returns_valid_response(self):
        """Test that prepare_next_actor returns correctly formatted response."""
        result = self.tools.prepare_next_actor(
            actor="expert1",
            reason="Test reason"
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["actor"], "expert1")
        self.assertEqual(result["reason"], "Test reason")
        self.assertEqual(result["status"], "ready")

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

    def test_get_actor_prompt_questioner(self):
        """Test prompt generation for questioner."""
        with patch('app.actor.ChatOllama'):
            moderator = Moderator(self.model_config, self.mock_discussion)
            prompt = moderator.get_actor_prompt(
            actor="questioner",
            topic="test topic",
            is_last_round=False,
            is_brief=True
        )
        
        self.assertIn("Ask a relevant question", prompt)
        self.assertIn("brief, focused response", prompt)

    def test_get_actor_prompt_expert_last_round(self):
        """Test prompt generation for expert in last round."""
        with patch('app.actor.ChatOllama'):
            moderator = Moderator(self.model_config, self.mock_discussion)
            prompt = moderator.get_actor_prompt(
            actor="expert1",
            topic="test topic",
            is_last_round=True,
            is_brief=False
        )
        
        self.assertIn("final summary", prompt)
        self.assertIn("detailed explanations", prompt)

    def test_get_actor_prompt_validator(self):
        """Test prompt generation for validator."""
        with patch('app.actor.ChatOllama'):
            moderator = Moderator(self.model_config, self.mock_discussion)
            prompt = moderator.get_actor_prompt(
            actor="validator",
            topic="test topic",
            is_last_round=False,
            is_brief=True
        )
        
        self.assertIn("Validate the recent questions and answers", prompt)
        self.assertIn("brief, focused response", prompt)

if __name__ == '__main__':
    unittest.main()
