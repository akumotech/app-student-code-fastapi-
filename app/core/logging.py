import logging
import sys
from typing import Optional
from pathlib import Path
from app.config import settings

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup application logging with proper formatting and handlers"""
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Set up root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            *([logging.FileHandler(log_file)] if log_file else [])
        ]
    )
    
    # Create application logger
    logger = logging.getLogger("akumo_api")
    
    # Set specific log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DATABASE_ECHO_SQL else logging.WARNING
    )
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a named logger for a specific module"""
    return logging.getLogger(f"akumo_api.{name}")

# Create main application logger
logger = get_logger("main") 