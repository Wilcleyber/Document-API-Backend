from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.schemas import LoginRequest, TokenResponse, TokenPayload
from src.auth.service import authenticate_user, create_access_token
from src.auth.dependencies import get_current_user
from src.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(payload: LoginRequest):
    """
    Autentica usuário com credenciais e retorna JWT.
    
    - **username**: nome de usuário
    - **password**: senha do usuário
    
    Retorna access_token com expiração configurada.
    """
    user = await authenticate_user(payload.username, payload.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials",
        )
    
    token_response = create_access_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
    )
    
    return token_response

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: TokenPayload = Depends(get_current_user)):
    """
    Logout do usuário.
    
    Implementação simples: o frontend remove o token.
    Para maior robustez, implementar blacklist (fora de escopo inicial).
    """
    logger.info(f"User logged out: {current_user.user_id}")
    return None

@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: TokenPayload = Depends(get_current_user)):
    """
    Retorna informações do usuário autenticado.
    Útil para validar token e retornar dados do user.
    """
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role,
    }