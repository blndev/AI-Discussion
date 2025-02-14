import unittest
from unittest.mock import Mock, patch
from app.actor import Actor

class TestActor(unittest.TestCase):
    """Test cases for the Actor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.model_config = {
            "model": "test-model",
            "model_params": {
                "temperature": 0.7,
                "top_p": 0.8
            }
        }
        # Mock discussion with history
        self.mock_discussion = Mock()
        self.mock_discussion.discussion_history = [
            {"actor": "System", "message": "Starting discussion"},
            {"actor": "Expert 1", "message": "Previous response"}
        ]

    def test_actor_initialization(self):
        """Test actor initialization with correct parameters."""
        with patch('app.actor.ChatOllama') as mock_chat_ollama:
            actor = Actor("Test Actor", "test role", self.model_config, self.mock_discussion)
            
            self.assertEqual(actor.name, "Test Actor")
            self.assertEqual(actor.role, "test role")
            self.assertEqual(actor.discussion, self.mock_discussion)
            
            # Verify ChatOllama was initialized with correct parameters
            mock_chat_ollama.assert_called_once_with(
                model=self.model_config["model"],
                temperature=self.model_config["model_params"]["temperature"],
                top_p=self.model_config["model_params"]["top_p"]
            )

    def test_get_context_returns_last_five_messages(self):
        """Test that get_context returns the last 5 messages from discussion history."""
        with patch('app.actor.ChatOllama') as mock_chat_ollama:
            # Create actor with mocked discussion
            actor = Actor("Test Actor", "test role", self.model_config, self.mock_discussion)
            
            # Create a history with more than 5 messages
            self.mock_discussion.discussion_history = [
                {"actor": "System", "message": f"Message {i}"} 
                for i in range(10)
            ]
            
            context = actor.get_context()
        
        self.assertEqual(len(context), 5)
        self.assertEqual(context[0]["message"], "Message 5")
        self.assertEqual(context[-1]["message"], "Message 9")

    def test_get_prompt_format(self):
        """Test that get_prompt returns correctly formatted prompt."""
        with patch('app.actor.ChatOllama') as mock_chat_ollama:
            # Create actor with mocked discussion
            actor = Actor("Test Actor", "test role", self.model_config, self.mock_discussion)
            prompt = actor.get_prompt("Test message")
        
        # Verify prompt contains all required components
        self.assertIn("You are Test Actor", prompt)
        self.assertIn("test role", prompt)
        self.assertIn("Previous context", prompt)
        self.assertIn("Starting discussion", prompt)  # From mock history
        self.assertIn("Previous response", prompt)    # From mock history
        self.assertIn("Test message", prompt)

    def test_respond_returns_llm_response(self):
        """Test that respond method returns LLM response content."""
        with patch('app.actor.ChatOllama') as mock_chat_ollama:
            # Setup mock LLM response
            mock_response = Mock()
            mock_response.content = "Test response"
            mock_chat_ollama.return_value.invoke.return_value = mock_response
            
            # Create new actor with mocked LLM
            actor = Actor("Test Actor", "test role", self.model_config, self.mock_discussion)
            
            response = actor.respond("Test message")
        
        self.assertEqual(response, "Test response")
        # Verify LLM was called with correct prompt
        mock_chat_ollama.return_value.invoke.assert_called_once()
        prompt_arg = mock_chat_ollama.return_value.invoke.call_args[0][0]
        self.assertIn("Test message", prompt_arg)

    def test_get_context_with_no_discussion(self):
        """Test that get_context handles case when no discussion is set."""
        with patch('app.actor.ChatOllama') as mock_chat_ollama:
            actor = Actor("Test Actor", "test role", self.model_config)
            context = actor.get_context()
        self.assertEqual(context, [])

if __name__ == '__main__':
    unittest.main()
