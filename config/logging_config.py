import logging

class LoggingConfig:
    """
    Configuration for logging.
    """
    @staticmethod
    def setup_logging():
        """
        Set up logging configuration.
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logging.info("Logging is configured.")