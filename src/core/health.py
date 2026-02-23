from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.db.connection import DatabasePool
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])

class HealthResponse(BaseModel):
    """Modelo de resposta de health check."""
    status: str  # "healthy" ou "unhealthy"
    version: str
    environment: str
    database: str  # "connected" ou "disconnected"

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Endpoint de health check.
    Verifica status da aplicação e conexão com banco de dados.
    """
    
    db_status = "disconnected"
    
    try:
        # Testa conexão com banco de dados
        result = await DatabasePool.fetch_one("SELECT 1")
        if result:
            db_status = "connected"
    except Exception as e:
        logger.warning(f"⚠️  Erro ao verificar banco de dados: {str(e)}")
        db_status = "disconnected"
    
    # Se DB desconectado, retorna unhealthy
    if db_status == "disconnected":
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "version": settings.app_version,
                "environment": settings.environment,
                "database": db_status,
            }
        )
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
        database=db_status,
    )

@router.get("/info")
async def app_info() -> dict:
    """Retorna informações da aplicação."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
    }