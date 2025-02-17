# AI-Discussion

An AI-powered discussion panel that creates engaging conversations between multiple AI actors on any topic using Ollama and LangChain. The system can run on CPU only, though responses may be slower compared to GPU execution.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Prerequisites

- Python 3.12 or higher
- Ollama installed and running locally (https://ollama.ai)

## Configuration

The application uses a `config.json` file for model settings:

```json
{
    "model": "llama3.1",
    "model_params": {
        "temperature": 0.7,
        "top_p": 0.8
    }
}
```

## Installation

1. Clone this repository
2. Run the setup script:
```bash
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Check for Ollama installation
- Pull the required llama3.1 model

## Usage

1. Start Ollama service
2. Run the application:
```bash
./start.sh
```

For debug logging:
```bash
python main.py --debug
```

3. The Gradio interface will open in your default web browser
4. Enter a topic and click "Start Discussion"
5. Watch the AI-powered discussion unfold in real-time
6. Use the Stop Discussion button to end the conversation

## AI Actors

The application features several AI actors in a structured discussion:

- 🤔 **Questioner**: Asks insightful questions to explore the topic
- 👨‍🔬 **Expert 1**: Provides detailed insights and answers
- 👩‍🔬 **Expert 2**: Offers additional perspectives and validates Expert 1's answers
- ✅ **Validator**: Ensures accuracy and relevance of the discussion
- 👨‍💼 **Moderator**: Manages conversation flow and participant selection

## Features

- Gradio web interface for easy interaction
- Real-time discussion updates
- Colored logging for better visibility
- Structured conversation flow
- Dynamic topic exploration
- Configurable model parameters

## Architecture

The application uses a modular architecture:

- **AIDiscussion**: Core discussion management
- **Actor**: Base class for AI participants
- **Moderator**: Specialized actor for flow control
- **GradioUI**: Web interface implementation

## Development

To extend or modify the application:

1. Update model settings in `config.json`
2. Modify actor behaviors in `app/actor.py`
3. Adjust discussion flow in `app/moderator.py`
4. Run tests: `python -m pytest tests/`
