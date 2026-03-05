"""
FastAPI middleware for centralized error handling.

This module provides:
- Exception handling middleware for consistent error responses
- Request logging middleware
- Error response formatting

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import traceback
import uuid

from services.error_handling import (
    VisionError,
    ErrorCode,
    format_error_response,
    log_error,
    log_info,
    logger
)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for centralized error handling and logging.
    
    Catches all unhandled exceptions and formats them into consistent
    JSON error responses.
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and handle any exceptions.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            HTTP response (either success or formatted error)
        """
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        try:
            # Log incoming request
            log_info(
                f"Incoming request: {request.method} {request.url.path}",
                context={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_host": request.client.host if request.client else None
                }
            )
            
            # Process the request
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except VisionError as e:
            # Handle custom VISION errors
            error_response = e.to_response()
            error_response["error"]["request_id"] = request_id
            
            status_code = self._get_status_code(e.code)
            
            return JSONResponse(
                status_code=status_code,
                content=error_response,
                headers={"X-Request-ID": request_id}
            )
            
        except Exception as e:
            # Handle unexpected exceptions
            log_error(e, context={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "traceback": traceback.format_exc()
            })
            
            error_response = format_error_response(e, include_details=False)
            error_response["error"]["request_id"] = request_id
            
            return JSONResponse(
                status_code=500,
                content=error_response,
                headers={"X-Request-ID": request_id}
            )
    
    def _get_status_code(self, error_code: ErrorCode) -> int:
        """
        Map error codes to HTTP status codes.
        
        Args:
            error_code: The error code from VisionError
            
        Returns:
            Appropriate HTTP status code
        """
        status_map = {
            # 400 Bad Request
            ErrorCode.INVALID_AUDIO_FORMAT: 400,
            ErrorCode.FILE_SIZE_EXCEEDED: 400,
            ErrorCode.INVALID_REQUEST: 400,
            ErrorCode.VALIDATION_ERROR: 400,
            
            # 401 Unauthorized
            ErrorCode.AUTHENTICATION_ERROR: 401,
            
            # 403 Forbidden
            ErrorCode.AUTHORIZATION_ERROR: 403,
            
            # 404 Not Found
            ErrorCode.NOT_FOUND: 404,
            
            # 500 Internal Server Error
            ErrorCode.INTERNAL_ERROR: 500,
            ErrorCode.UNKNOWN_ERROR: 500,
            ErrorCode.DATABASE_ERROR: 500,
            ErrorCode.AUDIO_PROCESSING_ERROR: 500,
            ErrorCode.PDF_GENERATION_ERROR: 500,
            ErrorCode.TRANSCRIPTION_ERROR: 500,
            
            # 502 Bad Gateway (external service errors)
            ErrorCode.SPEECH_TO_TEXT_ERROR: 502,
            ErrorCode.GEMINI_AI_ERROR: 502,
            ErrorCode.GEMINI_AI_UNAVAILABLE: 502,
            
            # 503 Service Unavailable
            ErrorCode.NETWORK_ERROR: 503,
            ErrorCode.CONNECTION_LOST: 503,
            
            # 504 Gateway Timeout
            ErrorCode.SPEECH_TO_TEXT_TIMEOUT: 504,
        }
        
        return status_map.get(error_code, 500)


def setup_error_handlers(app):
    """
    Set up exception handlers for a FastAPI application.
    
    Args:
        app: FastAPI application instance
        
    Requirements: 7.1, 7.2, 7.3, 7.4
    """
    from fastapi import HTTPException
    from fastapi.exceptions import RequestValidationError
    
    @app.exception_handler(VisionError)
    async def vision_error_handler(request: Request, exc: VisionError):
        """Handle VisionError exceptions."""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        error_response = exc.to_response()
        error_response["error"]["request_id"] = request_id
        
        status_code = ErrorHandlingMiddleware(app)._get_status_code(exc.code)
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers={"X-Request-ID": request_id}
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTPException."""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Map HTTP status codes to error codes
        code_map = {
            400: ErrorCode.INVALID_REQUEST,
            401: ErrorCode.AUTHENTICATION_ERROR,
            403: ErrorCode.AUTHORIZATION_ERROR,
            404: ErrorCode.NOT_FOUND,
            500: ErrorCode.INTERNAL_ERROR
        }
        
        error_code = code_map.get(exc.status_code, ErrorCode.UNKNOWN_ERROR)
        
        error_response = {
            "error": {
                "code": error_code.value,
                "message": exc.detail,
                "retry_possible": exc.status_code >= 500,
                "request_id": request_id
            }
        }
        
        log_error(exc, context={
            "request_id": request_id,
            "status_code": exc.status_code
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response,
            headers={"X-Request-ID": request_id}
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Extract validation error details
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        error_response = {
            "error": {
                "code": ErrorCode.VALIDATION_ERROR.value,
                "message": "Request validation failed",
                "details": {"validation_errors": errors},
                "retry_possible": False,
                "request_id": request_id
            }
        }
        
        log_error(exc, context={
            "request_id": request_id,
            "validation_errors": errors
        })
        
        return JSONResponse(
            status_code=422,
            content=error_response,
            headers={"X-Request-ID": request_id}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other unhandled exceptions."""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        log_error(exc, context={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "traceback": traceback.format_exc()
        })
        
        error_response = {
            "error": {
                "code": ErrorCode.INTERNAL_ERROR.value,
                "message": "An internal error occurred",
                "retry_possible": False,
                "request_id": request_id
            }
        }
        
        return JSONResponse(
            status_code=500,
            content=error_response,
            headers={"X-Request-ID": request_id}
        )
