from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable, Awaitable
import logging
import time

from app.config.security import security_config


class SecurityMiddleware:
    """Security middleware for protecting endpoints"""

    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope)
        start_time = time.time()

        # Add security headers to response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add security headers
                headers = message.get("headers", [])
                headers.append((b"x-frame-options", b"SAMEORIGIN"))
                headers.append((b"x-content-type-options", b"nosniff"))
                headers.append((b"x-xss-protection", b"1; mode=block"))
                headers.append((b"strict-transport-security", b"max-age=31536000; includeSubDomains"))
                message["headers"] = headers
            await send(message)

        # Process request
        try:
            response = await self.app(scope, receive, send_wrapper)
        except HTTPException as e:
            # Log security-related errors
            if e.status_code in [401, 403, 429]:  # Unauthorized, Forbidden, Too Many Requests
                self.logger.warning(f"Security-related HTTP exception: {e.status_code} for {request.url}")
            raise
        except Exception as e:
            # Log unexpected errors
            self.logger.error(f"Unexpected error in security middleware: {str(e)}")
            raise

        # Log request for security monitoring
        process_time = time.time() - start_time
        self.logger.info(
            f"SECURITY_LOG: {request.method} {request.url} - "
            f"IP: {request.client.host} - "
            f"Process Time: {process_time:.2f}s"
        )

        return response


def validate_api_key(api_key: str) -> bool:
    """Validate API key for protected endpoints"""
    if not api_key:
        return False
    return security_config.validate_api_key(api_key)


def require_api_key(request: Request) -> bool:
    """Decorator or utility function to require API key for specific routes"""
    api_key = request.headers.get("X-API-Key")
    if not validate_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return True