"""
Centralized error handling and logging utilities for the VISION system.

This module provides:
- Custom exception classes for different error types
- Consistent error response formatting
- Retry logic with exponential backoff for external API calls
- Graceful degradation for AI service failures
- Logging utility for error tracking

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import logging
import time
import functools
import traceback
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import json
import os


# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Create logger
logger = logging.getLogger('vision')
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Create console handler if not already present
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)


class ErrorCode(str, Enum):
    """Enumeration of error codes for consistent error identification."""
    # External API errors
    SPEECH_TO_TEXT_ERROR = "SPEECH_TO_TEXT_ERROR"
    SPEECH_TO_TEXT_TIMEOUT = "SPEECH_TO_TEXT_TIMEOUT"
    GEMINI_AI_ERROR = "GEMINI_AI_ERROR"
    GEMINI_AI_UNAVAILABLE = "GEMINI_AI_UNAVAILABLE"
    
    # Validation errors
    INVALID_AUDIO_FORMAT = "INVALID_AUDIO_FORMAT"
    FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"
    INVALID_REQUEST = "INVALID_REQUEST"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    
    # Processing errors
    AUDIO_PROCESSING_ERROR = "AUDIO_PROCESSING_ERROR"
    PDF_GENERATION_ERROR = "PDF_GENERATION_ERROR"
    TRANSCRIPTION_ERROR = "TRANSCRIPTION_ERROR"
    
    # Database errors
    DATABASE_ERROR = "DATABASE_ERROR"
    NOT_FOUND = "NOT_FOUND"
    
    # Network errors
    NETWORK_ERROR = "NETWORK_ERROR"
    CONNECTION_LOST = "CONNECTION_LOST"
    
    # Authentication errors
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    
    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class ErrorDetails:
    """Structured error details for logging and response."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    retry_possible: bool = False
    timestamp: Optional[str] = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "code": self.code,
            "message": self.message,
            "retry_possible": self.retry_possible
        }
        if self.details:
            result["details"] = self.details
        return result


class VisionError(Exception):
    """Base exception class for VISION system errors."""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retry_possible: bool = False,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.retry_possible = retry_possible
        self.original_exception = original_exception
        self.timestamp = datetime.utcnow().isoformat()
        
        # Log the error
        log_error(self)
    
    def to_error_details(self) -> ErrorDetails:
        """Convert to ErrorDetails for response formatting."""
        return ErrorDetails(
            code=self.code.value,
            message=self.message,
            details=self.details,
            retry_possible=self.retry_possible,
            timestamp=self.timestamp
        )
    
    def to_response(self) -> Dict[str, Any]:
        """Convert to API response format."""
        return {"error": self.to_error_details().to_dict()}


class ExternalAPIError(VisionError):
    """Exception for external API failures (Google Speech-to-Text, Gemini AI)."""
    
    def __init__(
        self,
        service: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        code = ErrorCode.SPEECH_TO_TEXT_ERROR if "speech" in service.lower() else ErrorCode.GEMINI_AI_ERROR
        super().__init__(
            code=code,
            message=f"{service} API error: {message}",
            details={"service": service, **(details or {})},
            retry_possible=True,
            original_exception=original_exception
        )


class ValidationError(VisionError):
    """Exception for validation failures."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details={"field": field, **(details or {})} if field else details,
            retry_possible=False
        )


class ProcessingError(VisionError):
    """Exception for processing failures."""
    
    def __init__(
        self,
        operation: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        code_map = {
            "audio": ErrorCode.AUDIO_PROCESSING_ERROR,
            "pdf": ErrorCode.PDF_GENERATION_ERROR,
            "transcription": ErrorCode.TRANSCRIPTION_ERROR
        }
        code = code_map.get(operation.lower(), ErrorCode.INTERNAL_ERROR)
        super().__init__(
            code=code,
            message=f"{operation} processing error: {message}",
            details={"operation": operation, **(details or {})},
            retry_possible=True,
            original_exception=original_exception
        )


class NetworkError(VisionError):
    """Exception for network-related failures."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            code=ErrorCode.NETWORK_ERROR,
            message=message,
            details=details,
            retry_possible=True,
            original_exception=original_exception
        )


def log_error(
    error: Union[Exception, VisionError],
    context: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR
) -> None:
    """
    Log an error with structured context information.
    
    Args:
        error: The exception to log
        context: Additional context information
        level: Logging level (default: ERROR)
        
    Requirements: 7.5
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "error_type": type(error).__name__,
        "message": str(error)
    }
    
    if isinstance(error, VisionError):
        log_data.update({
            "code": error.code.value,
            "details": error.details,
            "retry_possible": error.retry_possible
        })
        if error.original_exception:
            log_data["original_error"] = str(error.original_exception)
    
    if context:
        log_data["context"] = context
    
    # Add stack trace for non-VisionError exceptions
    if not isinstance(error, VisionError):
        log_data["traceback"] = traceback.format_exc()
    
    logger.log(level, json.dumps(log_data, default=str))


def log_info(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log an info message with optional context."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "message": message
    }
    if context:
        log_data["context"] = context
    logger.info(json.dumps(log_data, default=str))


def log_warning(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log a warning message with optional context."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "message": message
    }
    if context:
        log_data["context"] = context
    logger.warning(json.dumps(log_data, default=str))


# Type variable for generic function return type
T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Decorated function with retry logic
        
    Requirements: 7.1, 7.2
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        log_error(e, context={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "status": "failed_all_retries"
                        })
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    log_warning(
                        f"Retry attempt {attempt + 1}/{max_retries} for {func.__name__}",
                        context={
                            "error": str(e),
                            "delay_seconds": delay
                        }
                    )
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in retry logic")
        
        return wrapper
    return decorator


async def async_retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    *args,
    **kwargs
) -> T:
    """
    Async version of retry with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result of the function call
        
    Requirements: 7.1, 7.2
    """
    import asyncio
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            
            if attempt == max_retries:
                log_error(e, context={
                    "function": func.__name__,
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "status": "failed_all_retries"
                })
                raise
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            
            log_warning(
                f"Async retry attempt {attempt + 1}/{max_retries} for {func.__name__}",
                context={
                    "error": str(e),
                    "delay_seconds": delay
                }
            )
            
            await asyncio.sleep(delay)
    
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected state in async retry logic")


class GracefulDegradation:
    """
    Context manager for graceful degradation when AI services fail.
    
    Provides fallback behavior when Gemini AI or other services are unavailable.
    
    Requirements: 7.2
    """
    
    def __init__(
        self,
        service_name: str,
        fallback_value: Any = None,
        notify_user: bool = True
    ):
        """
        Initialize graceful degradation handler.
        
        Args:
            service_name: Name of the service for logging
            fallback_value: Value to return if service fails
            notify_user: Whether to include user notification in result
        """
        self.service_name = service_name
        self.fallback_value = fallback_value
        self.notify_user = notify_user
        self.degraded = False
        self.error_message = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.degraded = True
            self.error_message = str(exc_val)
            
            log_warning(
                f"Graceful degradation activated for {self.service_name}",
                context={
                    "error_type": exc_type.__name__ if exc_type else None,
                    "error_message": self.error_message,
                    "fallback_value_type": type(self.fallback_value).__name__
                }
            )
            
            # Suppress the exception
            return True
        return False
    
    def get_result(self, success_value: Any) -> Dict[str, Any]:
        """
        Get the result with degradation status.
        
        Args:
            success_value: Value to return if service succeeded
            
        Returns:
            Dictionary with result and degradation status
        """
        if self.degraded:
            result = {
                "value": self.fallback_value,
                "degraded": True,
                "service": self.service_name
            }
            if self.notify_user:
                result["message"] = f"{self.service_name} is temporarily unavailable. " \
                                   f"Showing limited results."
            return result
        
        return {
            "value": success_value,
            "degraded": False
        }


def format_error_response(
    error: Union[Exception, VisionError],
    include_details: bool = True
) -> Dict[str, Any]:
    """
    Format an error into a consistent JSON response structure.
    
    Args:
        error: The exception to format
        include_details: Whether to include detailed error information
        
    Returns:
        Formatted error response dictionary
        
    Requirements: 7.1, 7.2, 7.3, 7.4
    """
    if isinstance(error, VisionError):
        return error.to_response()
    
    # Handle standard exceptions
    error_details = ErrorDetails(
        code=ErrorCode.INTERNAL_ERROR.value,
        message=str(error) if include_details else "An internal error occurred",
        retry_possible=False
    )
    
    return {"error": error_details.to_dict()}


def create_error_response(
    code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    retry_possible: bool = False
) -> Dict[str, Any]:
    """
    Create a formatted error response.
    
    Args:
        code: Error code from ErrorCode enum
        message: Human-readable error message
        details: Additional error details
        retry_possible: Whether the operation can be retried
        
    Returns:
        Formatted error response dictionary
    """
    error_details = ErrorDetails(
        code=code.value,
        message=message,
        details=details,
        retry_possible=retry_possible
    )
    
    return {"error": error_details.to_dict()}
