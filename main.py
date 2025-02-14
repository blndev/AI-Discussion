import logging
import json
from app.ui import GradioUI
import colorlog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Reduce noise from third-party libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('gradio').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def load_config() -> dict:
    """Load configuration from config.json file."""
    try:
        with open('config.json') as f:
            config = json.load(f)
            logger.info(f"Loaded configuration: model={config['model']}")
            return config
    except FileNotFoundError:
        logger.error("config.json not found")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config.json: {e}")
        raise
    except KeyError as e:
        logger.error(f"Missing required configuration key: {e}")
        raise

def main():
    """Main entry point for the AI Discussion application."""
    try:
        config = load_config()
    
        ui = GradioUI(model_config=config)
        ui.launch()
    except Exception as e:
        logger.error(f"Failed to start application")

if __name__ == "__main__":
    main()
