"""Global exception handlers for consistent error responses."""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class APIError:
    """Standard API error response format."""

    @staticmethod
    def error_response(
        status_code: int,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a standardized error response."""
        response = {
            "error": {
                "message": message,
                "status_code": status_code
            }
        }

        if error_code:
            response["error"]["code"] = error_code

        if details:
            response["error"]["details"] = details

        return response


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with detailed information."""
    errors = []

    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })

    error_response = APIError.error_response(
        status_code=422,
        message="Validation failed",
        error_code="VALIDATION_ERROR",
        details={"errors": errors}
    )

    logger.warning(f"Validation error: {errors}")

    return JSONResponse(
        status_code=422,
        content=error_response
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """Handle HTTP exceptions with consistent format."""
    error_response = APIError.error_response(
        status_code=exc.status_code,
        message=exc.detail,
        error_code="HTTP_ERROR"
    )

    # Log errors for 5xx status codes
    if exc.status_code >= 500:
        logger.error(f"Server error: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions."""
    error_response = APIError.error_response(
        status_code=500,
        message="Internal server error",
        error_code="INTERNAL_ERROR"
    )

    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=error_response
    )