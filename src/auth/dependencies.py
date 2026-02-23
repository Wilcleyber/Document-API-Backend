from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from src.auth.service import decode_token
from src.auth.schemas import TokenPayload
from src.core.logging_config import get_logger

logger = get_logger(__name__)

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    """
    Dependency que extrai e valida token JWT da header Authorization.
    Usado em rotas protegidas.
    """
    token = credentials.credentials
    
    payload = decode_token(token)
    if not payload:
        logger.warning("Invalid or expired token attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_or_expired_token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

async def get_current_admin_user(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    Dependency que valida se usuário atual é ADMIN.
    Usado em rotas administrativas.
    """
    if current_user.role != "ADMIN":
        logger.warning(f"Unauthorized admin access attempt by user: {current_user.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin_access_required",
        )
    
    return current_user

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[TokenPayload]:
    """
    Dependency para rotas que aceitam token opcional.
    """
    if not credentials:
        return None
    
    payload = decode_token(credentials.credentials)
    return payload