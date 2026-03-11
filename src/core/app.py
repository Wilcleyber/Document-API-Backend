from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.core.config import settings
from src.core.logging_config import setup_logging, get_logger
from src.core.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware
from src.db.connection import DatabasePool
from src.db.migrations import MigrationManager
# Routers
from src.core.health import router as health_router
from src.users import users_router
from src.auth import auth_router
from src.nodes import nodes_router
from src.file_content import file_content_router
from src.navigation import navigation_router
from src.admin_ops import admin_ops_router
from src.docs import setup_docs

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager para startup/shutdown da aplicação."""
    
    # STARTUP
    logger.info(f"🚀 Iniciando {settings.app_name} v{settings.app_version}")
    logger.info(f"📍 Ambiente: {settings.environment}")
    
    try:
        # Inicializa pool de conexões
        await DatabasePool.initialize(settings)
        logger.info("✓ Pool de conexões inicializado")
        
        # Executa migrações
        await MigrationManager.run_all_migrations()
        logger.info("✓ Migrações executadas com sucesso")
        
    except Exception as e:
        logger.error(f"✗ Erro durante startup: {str(e)}")
        raise
    
    yield
    
    # SHUTDOWN
    logger.info("🛑 Encerrando aplicação...")
    
    try:
        await DatabasePool.close()
        logger.info("✓ Conexões fechadas com sucesso")
    except Exception as e:
        logger.error(f"✗ Erro durante shutdown: {str(e)}")

def create_app() -> FastAPI:
    """Factory function para criar e configurar a aplicação FastAPI."""
    
    # Setup logging
    setup_logging()
    
    # Criar app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="API para gerenciar arquivos de texto em estrutura hierárquica",
        lifespan=lifespan,
        debug=settings.debug,
    )
    
    # Middlewares
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.info(f"✓ CORS configurado para: {', '.join(settings.cors_origins)}")

    # Register routers used by the application
    app.include_router(health_router)
    app.include_router(users_router)
    app.include_router(auth_router)
    app.include_router(nodes_router)
    app.include_router(file_content_router)
    app.include_router(navigation_router)
    app.include_router(admin_ops_router)

    # Configure OpenAPI docs
    setup_docs(app)
    
    return app

# Instância global da app
app = create_app()