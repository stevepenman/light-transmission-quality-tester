"""
Logging configuration for Light Transmission Tester - SYNTHETIC DEMO
Provides structured logging with rotation and multiple output formats
"""
import logging
import os
from runtime_paths import data_directory
from logging.handlers import RotatingFileHandler
from datetime import datetime


class TesterLogger:
    """Centralized logging configuration for the application"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.log_dir = str(data_directory() / 'logs')
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir)
            except Exception as e:
                print(f"Warning: Could not create logs directory: {e}")
                raise
        
        self.setup_loggers()
    
    def setup_loggers(self):
        """Configure logging for different components"""
        
        # Main application logger
        self.app_logger = self._create_logger(
            'WallThicknessTester',
            os.path.join(self.log_dir, 'application.log'),
            logging.INFO
        )
        
        # Hardware logger (for sensor readings and GPIO)
        self.hardware_logger = self._create_logger(
            'Hardware',
            os.path.join(self.log_dir, 'hardware.log'),
            logging.DEBUG
        )
        
        # Email logger (for email operations)
        self.email_logger = self._create_logger(
            'Email',
            os.path.join(self.log_dir, 'email.log'),
            logging.INFO
        )
        
        # Error logger (only errors and critical)
        self.error_logger = self._create_logger(
            'Errors',
            os.path.join(self.log_dir, 'errors.log'),
            logging.ERROR
        )
    
    def _create_logger(self, name, log_file, level):
        """Create a logger with file and console handlers"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # Capture all levels
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # File handler with rotation (5MB max, keep 5 backup files)
        try:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=5*1024*1024,  # 5MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            
            # Detailed format for file logs
            file_formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not create file handler for {name}: {e}")
        
        # Console handler for warnings and above
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Simpler format for console
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def get_logger(self, component='app'):
        """Get logger for specific component"""
        loggers = {
            'app': self.app_logger,
            'hardware': self.hardware_logger,
            'email': self.email_logger,
            'error': self.error_logger
        }
        return loggers.get(component, self.app_logger)


# Convenience function to get logger
def get_logger(component='app'):
    """
    Get a logger instance for the specified component
    
    Args:
        component: 'app', 'hardware', 'email', or 'error'
    
    Returns:
        logging.Logger instance
    """
    tester_logger = TesterLogger()
    return tester_logger.get_logger(component)


# Log decorator for functions
def log_function_call(logger=None):
    """Decorator to log function entry and exit"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if logger is None:
                log = get_logger('app')
            else:
                log = logger
            
            log.debug(f"Entering {func.__name__}")
            try:
                result = func(*args, **kwargs)
                log.debug(f"Exiting {func.__name__} successfully")
                return result
            except Exception as e:
                log.error(f"Error in {func.__name__}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator
