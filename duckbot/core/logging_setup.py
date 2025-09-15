# duckbot/logging_setup.py
import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

# Default log level from environment
DEFAULT_LOG_LEVEL = os.getenv("DUCKBOT_LOG_LEVEL", "WARNING").upper()
LOG_DIR = Path(__file__).parent.parent / "logs"

class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)

def setup_logging(name: str = "duckbot", level: str = None) -> logging.Logger:
    """Setup centralized logging configuration"""
    
    # Use provided level or environment variable
    log_level = (level or DEFAULT_LOG_LEVEL).upper()
    numeric_level = getattr(logging, log_level, logging.WARNING)
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(numeric_level)
    
    # Create logs directory
    LOG_DIR.mkdir(exist_ok=True)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = ColoredFormatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler with rotation
    log_file = LOG_DIR / f"{name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # Always log all levels to file
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance with standardized configuration"""
    if name is None:
        name = "duckbot"
    
    # Use module name if called from a module
    frame = sys._getframe(1)
    if 'module' in frame.f_globals or '__name__' in frame.f_globals:
        module_name = frame.f_globals.get('__name__', name)
        if module_name != '__main__' and '.' in module_name:
            name = module_name
    
    return setup_logging(name)

def log_system_info(logger: logging.Logger):
    """Log basic system information"""
    logger.info(f"DuckBot v3.0.4 starting up")
    logger.info(f"Python version: {sys.version.split()[0]}")
    logger.info(f"Log level: {logger.level} ({logging.getLevelName(logger.level)})")
    logger.info(f"Log directory: {LOG_DIR}")

# Create default logger instance
default_logger = get_logger("duckbot")

# Utility functions for quick logging
def debug(msg, *args, **kwargs):
    default_logger.debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    default_logger.info(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    default_logger.warning(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    default_logger.error(msg, *args, **kwargs)

def critical(msg, *args, **kwargs):
    default_logger.critical(msg, *args, **kwargs)

def exception(msg, *args, **kwargs):
    default_logger.exception(msg, *args, **kwargs)

# Initialize logging when imported
if __name__ != "__main__":
    # Only log system info if explicitly called, not on import
    pass