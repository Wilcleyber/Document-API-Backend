import uvicorn
from src.core.app import app
from src.core.health import router as health_router
from src.users import users_router
from src.auth import auth_router
from src.nodes import nodes_router
from src.file_content import file_content_router
from src.navigation import navigation_router
from src.admin_ops import admin_ops_router
from src.core.config import settings
from src.core.logging_config import get_logger
from src.docs import setup_docs

logger = get_logger(__name__)

# Registra routers
app.include_router(health_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(nodes_router)
app.include_router(file_content_router)
app.include_router(navigation_router)
app.include_router(admin_ops_router)

# Setup OpenAPI docs (tags, error shapes, examples)
setup_docs(app)   # <-- added

if __name__ == "__main__":
    logger.info(f"🌐 Iniciando servidor em http://localhost:8000")
    logger.info(f"📚 Documentação em http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )