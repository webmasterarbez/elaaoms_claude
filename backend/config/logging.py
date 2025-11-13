"""
Logging configuration for ELAAOMS with structured logging, request ID tracking,
and API key masking per constitution requirements.
"""

import logging
import sys
import re
from typing import Any, Dict


class APIKeyMaskingFilter(logging.Filter):
    """
    Filter to mask API keys in log messages.
    
    Masks API keys to maximum 8 characters per constitution requirements.
    Examples:
    - "sk-1234567890abcdef" -> "sk-1234..."
    - "elevenlabs_key_abc123xyz" -> "elevenl..."
    """

    # Patterns for common API key formats
    API_KEY_PATTERNS = [
        (r'sk-[a-zA-Z0-9]{20,}', lambda m: f"{m.group()[:8]}..."),  # OpenAI keys
        (r'elevenlabs_[a-zA-Z0-9]{20,}', lambda m: f"{m.group()[:8]}..."),  # ElevenLabs keys
        (r'[a-zA-Z0-9]{32,}', lambda m: f"{m.group()[:8]}..."),  # Generic long keys
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Mask API keys in log record message."""
        if hasattr(record, 'msg') and record.msg:
            record.msg = self._mask_api_keys(str(record.msg))
        
        if hasattr(record, 'args') and record.args:
            # Mask API keys in format arguments
            masked_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    masked_args.append(self._mask_api_keys(arg))
                else:
                    masked_args.append(arg)
            record.args = tuple(masked_args)
        
        return True

    def _mask_api_keys(self, text: str) -> str:
        """Mask API keys in text string."""
        masked = text
        for pattern, replacement in self.API_KEY_PATTERNS:
            masked = re.sub(pattern, replacement, masked)
        return masked


class RequestIDFilter(logging.Filter):
    """
    Filter to add request ID to log records.
    
    Extracts request ID from log message format [request_id] or adds it
    if missing from context.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request ID to log record if available."""
        # Request ID is typically included in the message format [request_id]
        # This filter ensures it's available in the record for structured logging
        if not hasattr(record, 'request_id'):
            # Try to extract from message
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                match = re.search(r'\[([a-f0-9-]{36})\]', record.msg)
                if match:
                    record.request_id = match.group(1)
                else:
                    record.request_id = None
            else:
                record.request_id = None
        return True


def setup_logging(
    log_level: str = "INFO",
    debug: bool = False,
    format_string: str = None
) -> None:
    """
    Configure structured logging for ELAAOMS.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        debug: Enable debug mode (sets level to DEBUG)
        format_string: Custom format string (optional)
    
    Sets up:
    - Structured logging with request ID tracking
    - API key masking (max 8 characters)
    - Console handler with formatted output
    """
    # Determine log level
    level = logging.DEBUG if debug else getattr(logging, log_level.upper(), logging.INFO)
    
    # Default format with request ID support
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(request_id)s] - %(message)s"
        )
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Add filters
    console_handler.addFilter(APIKeyMaskingFilter())
    console_handler.addFilter(RequestIDFilter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with request ID support.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    return logger

