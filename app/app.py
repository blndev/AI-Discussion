from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class App(ABC):
    """
    Base class for AI Discussion applications.
    Provides a common interface for different UI implementations.
    """
    
    def __init__(self, model_config: dict):
        """
        Initialize the application.
        
        Args:
            model_config (dict): Configuration for the LLM model
        """
        logger.info("Initializing application")
        self.model_config = model_config

    @abstractmethod
    def launch(self):
        """
        Launch the application interface.
        Must be implemented by subclasses.
        """
        pass
