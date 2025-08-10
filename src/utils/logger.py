"""
Logging utilities for UK Solicitors Data Processing
"""

import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import yaml
from colorama import Fore, Back, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE + Style.BRIGHT,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        record.name = f"{Fore.BLUE}{record.name}{Style.RESET_ALL}"
        return super().format(record)


class LoggerManager:
    """Centralized logging configuration and management"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/settings.yaml")
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration from YAML file"""
        try:
            # Ensure logs directory exists
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            # Load configuration
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    logging_config = config.get('logging', {})
            else:
                logging_config = self._get_default_config()
            
            # Apply configuration
            logging.config.dictConfig(logging_config)
            
        except Exception as e:
            # Fallback to basic configuration
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stdout),
                    logging.FileHandler('logs/app.log')
                ]
            )
            logging.error(f"Failed to load logging configuration: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default logging configuration"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
                'colored': {
                    '()': ColoredFormatter,
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'colored',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'standard',
                    'filename': 'logs/app.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5
                }
            },
            'root': {
                'level': 'INFO',
                'handlers': ['console', 'file']
            }
        }
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the specified name"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]
    
    def set_level(self, level: str):
        """Set logging level for all loggers"""
        level_obj = getattr(logging, level.upper(), logging.INFO)
        for logger in self.loggers.values():
            logger.setLevel(level_obj)


# Global logger manager instance
_logger_manager = None


def setup_logging(config_path: Optional[Path] = None) -> LoggerManager:
    """Setup logging and return logger manager"""
    global _logger_manager
    _logger_manager = LoggerManager(config_path)
    return _logger_manager


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager.get_logger(name)


class ProgressLogger:
    """Logger for tracking progress of long-running operations"""
    
    def __init__(self, logger: logging.Logger, operation: str, total: int):
        self.logger = logger
        self.operation = operation
        self.total = total
        self.current = 0
        self.logger.info(f"Starting {operation} - {total} items to process")
    
    def update(self, increment: int = 1, message: Optional[str] = None):
        """Update progress"""
        self.current += increment
        progress = (self.current / self.total) * 100
        
        base_msg = f"{self.operation}: {self.current}/{self.total} ({progress:.1f}%)"
        if message:
            base_msg += f" - {message}"
            
        self.logger.info(base_msg)
    
    def complete(self, message: Optional[str] = None):
        """Mark operation as complete"""
        base_msg = f"Completed {self.operation} - {self.total} items processed"
        if message:
            base_msg += f" - {message}"
        self.logger.info(base_msg)


def log_exception(logger: logging.Logger, exception: Exception, context: Optional[str] = None):
    """Log exception with context"""
    msg = f"Exception occurred: {type(exception).__name__}: {str(exception)}"
    if context:
        msg = f"{context} - {msg}"
    logger.exception(msg)


def log_performance(logger: logging.Logger, operation: str, duration: float, **kwargs):
    """Log performance metrics"""
    msg = f"Performance: {operation} took {duration:.3f}s"
    if kwargs:
        details = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        msg += f" ({details})"
    logger.info(msg)


# Decorator for logging function calls
def log_calls(logger_name: str = None):
    """Decorator to log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                log_exception(logger, e, f"Error in {func.__name__}")
                raise
        return wrapper
    return decorator