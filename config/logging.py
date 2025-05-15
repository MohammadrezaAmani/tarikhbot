import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import SETTINGS

# Get the log level from settings
LOG_LEVEL = getattr(logging, SETTINGS["app"]["log_level"])

# Base project directory
BASE_DIR = Path(__file__).parent.parent

# Log directory
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure the logging
def configure_logging():
    """Configure the logging system for the application."""
    logging_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(filename)s:%(lineno)d - %(message)s"
    )
    
    # Create formatters
    console_formatter = logging.Formatter(logging_format)
    file_formatter = logging.Formatter(logging_format)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    
    # Clear existing handlers
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler - general log
    general_log_file = LOG_DIR / "app.log"
    general_file_handler = RotatingFileHandler(
        general_log_file, 
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    general_file_handler.setLevel(LOG_LEVEL)
    general_file_handler.setFormatter(file_formatter)
    root_logger.addHandler(general_file_handler)
    
    # Error log - separate file for errors
    error_log_file = LOG_DIR / "error.log"
    error_file_handler = RotatingFileHandler(
        error_log_file, 
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_file_handler)
    
    # Set specific loggers
    # Suppress verbose loggers
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("tortoise").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    
    # Create component-specific loggers
    create_component_logger("bot")
    create_component_logger("tasks")
    create_component_logger("finance")
    create_component_logger("google")
    create_component_logger("users")
    
    return root_logger

def create_component_logger(component_name):
    """Create a logger for a specific component with its own file."""
    logger = logging.getLogger(component_name)
    
    # Component-specific log file
    component_log_file = LOG_DIR / f"{component_name}.log"
    component_file_handler = RotatingFileHandler(
        component_log_file, 
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3
    )
    component_file_handler.setLevel(LOG_LEVEL)
    component_file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(component_file_handler)
    
    return logger

def get_logger(name):
    """Get a logger by name."""
    return logging.getLogger(name)

# Logger instances for import
app_logger = get_logger("app")
bot_logger = get_logger("bot")
tasks_logger = get_logger("tasks")
finance_logger = get_logger("finance")
google_logger = get_logger("google")
users_logger = get_logger("users")