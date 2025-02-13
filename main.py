from gradio_ui import GradioUI
import logging

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
    logger.info("Starting AI Discussion Panel")
    
    ui = GradioUI()
    ui.launch()

if __name__ == "__main__":
    main()
