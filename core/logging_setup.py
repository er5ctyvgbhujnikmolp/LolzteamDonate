import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging():
    """Set up application logging.

    Returns:
        logging.Logger: Root logger
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create log file with timestamp
    log_filename = f"lolzteam_donate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_filepath = logs_dir / log_filename

    # Configure logging
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

    # Add file handler
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(log_format))

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    root_logger.info(f"Logging initialized, saving to {log_filepath}")

    return root_logger
