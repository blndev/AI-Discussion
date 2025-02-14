# AI Discussion Panel

This application creates an AI-powered discussion panel with 5 different actors discussing a user-provided topic using Ollama, LangChain, and multiple UI options.

## Prerequisites

- Python 3.12
- Ollama installed and running locally (with playground model)

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Ensure Ollama is running with the playground model:
```bash
ollama run playground
```

## Usage

The application provides two user interface options:

### Gradio Web Interface
1. Start the web interface:
```bash
python main.py
```
2. The Gradio interface will open in your default web browser
3. Enter a topic in the text box and click "Start Discussion"
4. Watch the AI-powered discussion unfold in real-time
5. Use the Stop Discussion button at any time to end the conversation

### Console Interface
1. Start the console interface:
```bash
python console_ui.py
```
2. Enter topics for discussion when prompted
3. Watch the discussion unfold in the terminal
4. Type 'quit' to exit the program

## Controls

### Gradio Interface
- **Start Discussion**: Begin a new AI-powered discussion on your chosen topic
- **Stop Discussion**: End the current discussion at any point
- **Topic Input**: Enter any topic you'd like the AI actors to discuss

### Console Interface
- Enter a topic when prompted
- On Windows: Press 'q' to stop the current discussion
- On Unix/Linux: Type 'q' and press Enter to stop the current discussion
- Type 'quit' to exit the program

## AI Actors

The application features 5 AI actors in a structured discussion:

- 🤔 **Questioner**: Asks insightful questions about the topic
- 👨‍🔬 **Expert 1**: Provides detailed answers
- 👩‍🔬 **Expert 2**: Enhances or optimizes Expert 1's answers
- ✅ **Validator**: Validates questions and answers for relevance and accuracy
- 👨‍💼 **Moderator**: Manages the conversation flow and decides who speaks next

## Features

- Multiple UI options (Gradio web interface and console)
- Real-time discussion updates
- Clear role identification for each participant
- Structured conversation flow managed by the Moderator
- Automatic topic exploration through multiple perspectives
- Maximum 20 rounds of discussion

## Architecture

The application is designed with a clean separation of concerns:

- **AIDiscussion**: Core class handling the AI actors and discussion logic
- **GradioUI**: Web interface implementation using Gradio
- **ConsoleUI**: Simple terminal-based interface

The AIDiscussion class can be easily integrated with other UI implementations by using its callback mechanism:

```python
def your_callback(actor: str, message: str):
    # Handle the message in your UI
    pass

discussion = AIDiscussion()
discussion.start_discussion("your topic", callback=your_callback)
