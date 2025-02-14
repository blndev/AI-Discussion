#!/bin/bash

# Exit on error
set -e

echo "Setting up AI-Discussion..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 is required but not installed. Please install Python3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is required but not installed. Please install pip3 and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install/upgrade requirements
echo "Installing/upgrading dependencies..."
pip install -r requirements.txt

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama is required but not installed."
    echo "Please install Ollama from: https://ollama.ai/"
    echo "Then run: ollama pull \$(python3 -c \"import json; print(json.load(open('config.json'))['model'])\")"
    exit 1
fi

# Read model from config
if [ ! -f "config.json" ]; then
    echo "config.json not found"
    exit 1
fi

MODEL=$(python3 -c "import json; print(json.load(open('config.json'))['model'])")
if [ $? -ne 0 ]; then
    echo "Failed to read model from config.json"
    exit 1
fi

# Pull/update the model
echo "Pulling/updating $MODEL model..."
ollama pull $MODEL

echo "Setup complete! You can now run ./start.sh to start the application."
