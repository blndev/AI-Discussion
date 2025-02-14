from app.ui import GradioUI
import logging

# Global configuration
CONFIG = {
    "model": "llama3.2",  # Base model to use
    "model_params": {
        "temperature": 0.7,
        "top_p": 0.9
    }
}

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('gradio').setLevel(logging.WARNING)

def main():
    """Entry point of the application."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"Starting AI Discussion Panel with model: {CONFIG['model']}")
    
    ui = GradioUI(model_config=CONFIG)
    ui.launch()

if __name__ == "__main__":
    main()
