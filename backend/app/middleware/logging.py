"""
Request/Response logging middleware.

This middleware logs all incoming requests and outgoing responses
for debugging and monitoring purposes.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.

    Logs include:
    - Request method and path
    - Request headers (sanitized)
    - Response status code
    - Response time
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log details.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response from the route handler
        """
        # Record start time
        start_time = time.time()

        # Extract request info
        method = request.method
        path = request.url.path
        client = request.client.host if request.client else "unknown"

        # Log the request
        logger.info(f"Request started: {method} {path} from {client}")

        # Process the request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = (time.time() - start_time) * 1000  # Convert to ms

            # Add custom header with processing time
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

            # Log the response
            logger.info(
                f"Request completed: {method} {path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.2f}ms"
            )

            return response

        except Exception as e:
            # Calculate processing time
            process_time = (time.time() - start_time) * 1000

            # Log the error
            logger.error(
                f"Request failed: {method} {path} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.2f}ms"
            )

            # Re-raise the exception to be handled by error handlers
            raise
