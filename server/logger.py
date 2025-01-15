"""Logging configuration for the BookChat server."""

import os
import logging

def setup_logging():
    """Configure logging with multiple handlers and levels."""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)

    # Configure formats
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    console_format = '%(asctime)s - %(levelname)s - %(message)s'

    # Remove existing handlers
    root = logging.getLogger()
    for handler in root.handlers:
        root.removeHandler(handler)

    # Set up file handlers
    handlers = {
        'debug': (logging.FileHandler('logs/debug.log'), logging.DEBUG),
        'info': (logging.FileHandler('logs/info.log'), logging.INFO),
        'error': (logging.FileHandler('logs/error.log'), logging.ERROR),
        'console': (logging.StreamHandler(), logging.ERROR)
    }

    # Configure handlers
    for name, (handler, level) in handlers.items():
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(
            console_format if name == 'console' else log_format
        ))
        root.addHandler(handler)

    # Configure git logger
    git_logger = logging.getLogger('git')
    git_logger.setLevel(logging.INFO)
    git_handler = logging.FileHandler('logs/git.log')
    git_handler.setFormatter(logging.Formatter(log_format))
    git_logger.addHandler(git_handler)
    git_logger.propagate = False

    # Set root logger level
    root.setLevel(logging.DEBUG)

    return logging.getLogger('bookchat')
