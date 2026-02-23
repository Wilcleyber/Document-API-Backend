import logging
import time
import uuid
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requisições (BaseHTTPMiddleware)."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                "Erro não tratado",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
            )
            return JSONResponse(
                status_code=500, content={"detail": "Internal Server Error", "request_id": request_id}
            )

        process_time = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s",
                "client": request.client.host if request.client else None,
            },
        )

        response.headers["X-Request-ID"] = request_id
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware para tratamento de erros global (BaseHTTPMiddleware)."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error("Erro na requisição: %s", str(e), exc_info=True, extra={"path": request.url.path})
            return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})