import logging
from datetime import datetime

class LoggingConfig:
    """
    Configuration for logging.
    """
    @staticmethod
    def setup_logging(log_to_file: bool = False):
        """
        Set up logging configuration.

        Parameters:
        log_to_file (bool): If True, logs will also be written to a file named
                            '<current_datetime>-beryl.log'. Defaults to False.
        """
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        log_level = logging.INFO

        if log_to_file:
            log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-beryl.log")
            logging.basicConfig(
                level=log_level,
                format=log_format,
                handlers=[
                    logging.StreamHandler(),  # Log to console
                    logging.FileHandler(log_filename),  # Log to file
                ],
            )
            logging.info(f"Logging is configured. Logs are being written to {log_filename}.")
        else:
            logging.basicConfig(
                level=log_level,
                format=log_format,
            )
            logging.info("Logging is configured.")