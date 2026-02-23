from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.core.config import settings

tags_metadata = [
    {"name": "auth", "description": "Authentication endpoints (login, logout)."},
    {"name": "users", "description": "User registration and profile endpoints."},
    {"name": "nodes", "description": "Folder and file metadata management (ADMIN operations protected)."},
    {"name": "files", "description": "File content read/write endpoints."},
    {"name": "navigation", "description": "Tree navigation helpers: breadcrumbs, search, recursive listing."},
    {"name": "admin", "description": "Administrative operations (ADMIN-only)."},
    {"name": "health", "description": "Health and info endpoints."},
]

def setup_docs(app: FastAPI) -> None:
    """
    Customize OpenAPI schema: tags, reusable error responses and components.
    Attach standardized HTTP exception handler for consistent error shape.
    """
    def custom_openapi():
        if getattr(app, "openapi_schema", None):
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=settings.app_name,
            version=settings.app_version,
            description="TextFile Manager API — contract and examples for front-end integration.",
            routes=app.routes,
            tags=tags_metadata,
        )
        # components: standard error schema + reusable responses
        comps = openapi_schema.setdefault("components", {})
        schemas = comps.setdefault("schemas", {})
        schemas["ErrorResponse"] = {
            "title": "ErrorResponse",
            "type": "object",
            "properties": {
                "detail": {"type": "string"},
                "code": {"type": "string", "nullable": True},
            },
            "required": ["detail"],
        }
        responses = comps.setdefault("responses", {})
        responses["UnauthorizedError"] = {
            "description": "Authentication required",
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}
            },
        }
        responses["ForbiddenError"] = {
            "description": "Permission denied",
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}
            },
        }
        responses["NotFoundError"] = {
            "description": "Resource not found",
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}
            },
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Consistent HTTP exception shape
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        payload = {"detail": exc.detail if isinstance(exc.detail, str) else str(exc.detail)}
        # if detail is dict with code, try to surface code
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            payload["code"] = exc.detail.get("code")
        return JSONResponse(status_code=exc.status_code, content=payload)

    # Generic exception handler (avoid leaking internals)
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"detail": "internal_server_error"})