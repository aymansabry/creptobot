import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from typing import Optional, Dict, Any

class BotLogger:
    def __init__(self, name: str = 'arbitrage_bot', log_dir: str = 'logs'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,
            backupCount=7
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.logger.error(message, extra=extra)
    
    def exception(self, message: str, exc_info: Exception):
        self.logger.exception(message, exc_info=exc_info)

logger = BotLogger().logger
