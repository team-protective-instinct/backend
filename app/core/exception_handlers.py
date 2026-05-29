import logging
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette import status


logger = logging.getLogger(__name__)


async def http_exception_handler(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    if not isinstance(exception, StarletteHTTPException):
        return await unhandled_exception_handler(request, exception)

    detail = jsonable_encoder(exception.detail)
    return JSONResponse(
        status_code=exception.status_code,
        content=_error_response(
            detail=detail,
            path=request.url.path,
        ),
        headers=getattr(exception, "headers", None),
    )


async def validation_exception_handler(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    if not isinstance(exception, RequestValidationError):
        return await unhandled_exception_handler(request, exception)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=_error_response(
            detail=jsonable_encoder(exception.errors()),
            path=request.url.path,
        ),
    )


async def unhandled_exception_handler(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled exception during request: %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_response(
            detail="Internal server error",
            path=request.url.path,
        ),
    )


def _error_response(
    *,
    detail: Any,
    path: str,
) -> dict[str, Any]:
    return {
        "detail": detail,
        "path": path,
    }
