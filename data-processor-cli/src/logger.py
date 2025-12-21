import logging
import logging.handlers
import os
import sys

def setup_logger(name="data_processor", log_dir="logs", level=logging.INFO):
    """
    Sets up a comprehensive logger with console and file handlers.
    
    Args:
        name (str): Name of the logger.
        log_dir (str): Directory to store log files.
        level (int): Logging level (default: logging.INFO).
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Ensure log directory exists
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if function is called multiple times
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
    )

    # 1. Rotating File Handler (Keeps history, good for post-mortem)
    log_file_path = os.path.join(log_dir, "processor.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=10*1024*1024, backupCount=5  # 10MB per file, 5 backups
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG) # Capture everything in file

    # 2. Console Handler (Immediate feedback for CLI user)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level) # Respect requested level for console

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
