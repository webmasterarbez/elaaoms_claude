"""
Middleware for request ID tracking and error handling.
"""

import uuid
import logging
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and track request IDs for all requests.
    
    Adds a unique request ID to each request:
    - Generates UUID if not present in headers
    - Stores in request state for access in route handlers
    - Includes in response headers (X-Request-ID)
    """

    def __init__(self, app: ASGIApp):
        """Initialize request ID middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add request ID.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
        
        Returns:
            Response with X-Request-ID header
        """
        # Check if request ID already exists in headers
        request_id = request.headers.get("X-Request-ID")
        
        if not request_id:
            # Generate new request ID
            request_id = str(uuid.uuid4())
        
        # Store in request state for access in handlers
        request.state.request_id = request_id
        
        # Add to logger context (for structured logging)
        logger_context = {"request_id": request_id}
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for consistent error response formatting.
    
    Catches unhandled exceptions and formats them consistently:
    - Extracts request ID from request state
    - Formats error response with status, message, request_id
    - Logs errors with full context
    """

    def __init__(self, app: ASGIApp):
        """Initialize error handling middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle errors consistently.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
        
        Returns:
            Response with consistent error format on exception
        """
        try:
            response = await call_next(request)
            return response
        
        except Exception as e:
            # Get request ID from state (if available)
            request_id = getattr(request.state, "request_id", None)
            if not request_id:
                request_id = str(uuid.uuid4())
            
            # Log error with full context
            logger.error(
                f"[{request_id}] Unhandled exception: {str(e)}",
                exc_info=True,
                extra={"request_id": request_id}
            )
            
            # Return consistent error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "message": "Internal server error",
                    "request_id": request_id,
                    "error_code": "INTERNAL_ERROR"
                }
            )

