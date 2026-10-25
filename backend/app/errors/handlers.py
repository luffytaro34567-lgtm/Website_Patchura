"""Centralised exception handlers for FastAPI."""
from __future__ import annotations

import structlog
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger(__name__)


def _error_envelope(status_code: int, message: str, detail=None) -> dict:
    payload = {
        "success": False,
        "detail": message,
        "error": {"code": status_code, "message": message},
    }
    if detail is not None:
        payload["error"]["detail"] = detail
    return payload


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_envelope(exc.status_code, str(exc.detail)),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = jsonable_encoder(exc.errors())
        logger.warning("Validation error", errors=errors, path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_envelope(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Request validation failed",
                detail=errors,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            exc_type=type(exc).__name__,
            path=request.url.path,
            exc_info=True,
        )
        # Never expose internal details in the response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_envelope(500, "An internal server error occurred"),
        )
