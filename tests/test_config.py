import unittest
import json
import os
from unittest.mock import patch, mock_open
from main import load_config

class TestConfig(unittest.TestCase):
    """Test cases for configuration loading."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_config = {
            "model": "llama3.1",
            "model_params": {
                "temperature": 0.7,
                "top_p": 0.8
            }
        }

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        mock_file = mock_open(read_data=json.dumps(self.valid_config))
        with patch('builtins.open', mock_file):
            config = load_config()
            self.assertEqual(config['model'], 'llama3.1')
            self.assertEqual(config['model_params']['temperature'], 0.7)
            self.assertEqual(config['model_params']['top_p'], 0.8)

    def test_file_not_found(self):
        """Test handling of missing config file."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            with self.assertRaises(FileNotFoundError):
                load_config()

    def test_invalid_json(self):
        """Test handling of invalid JSON in config file."""
        mock_file = mock_open(read_data='invalid json content')
        with patch('builtins.open', mock_file):
            with self.assertRaises(json.JSONDecodeError):
                load_config()

    def test_missing_required_keys(self):
        """Test handling of missing required configuration keys."""
        invalid_config = {
            "model_params": {
                "temperature": 0.7
            }
        }
        mock_file = mock_open(read_data=json.dumps(invalid_config))
        with patch('builtins.open', mock_file):
            with self.assertRaises(KeyError):
                load_config()

if __name__ == '__main__':
    unittest.main()
