#!/bin/bash

# Exit on error
set -e

# Activate virtual environment
source venv/bin/activate

# Check if Ollama service is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Ollama service is not running."
    echo "Please start Ollama service first:"
    echo "  Linux/Mac: systemctl start ollama"
    echo "  Windows: Start Ollama from the system tray"
    exit 1
fi

echo "Starting AI-Discussion..."

# Start the application
python -m app.main

# Deactivate virtual environment on exit
deactivate
