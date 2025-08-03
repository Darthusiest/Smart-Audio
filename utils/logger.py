import sys
from pathlib import Path
from loguru import logger
from config import LOGGING_SETTINGS, LOGS_DIR

def setup_logger():
    """Configure the logger with custom settings"""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=LOGGING_SETTINGS["format"],
        level=LOGGING_SETTINGS["level"],
        colorize=True
    )
    
    # Add file handler
    log_file = LOGS_DIR / "app.log"
    logger.add(
        log_file,
        format=LOGGING_SETTINGS["format"],
        level=LOGGING_SETTINGS["level"],
        rotation=LOGGING_SETTINGS["rotation"],
        retention=LOGGING_SETTINGS["retention"],
        compression="zip"
    )
    
    return logger

def get_logger(name: str = None):
    """Get a logger instance with optional name"""
    if name:
        return logger.bind(name=name)
    return logger

# Initialize logger
setup_logger() 