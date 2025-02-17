import logging
import colorlog

def setup_logging(debug: bool = False):
    """Configure colored logging for the entire application.
    
    Args:
        debug (bool): If True, sets log level to DEBUG. Otherwise, uses INFO level.
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove any existing handlers
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    # Configure colored logging
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('gradio').setLevel(logging.WARNING)
