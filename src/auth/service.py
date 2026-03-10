import jwt
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from typing import Optional
from src.db.connection import DatabasePool
from src.auth.schemas import TokenResponse, TokenPayload
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    return bcrypt.verify(plain_password, hashed_password)

async def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Autentica usuário verificando credenciais.
    Retorna dados do usuário se válido, None caso contrário.
    """
    q = """
        SELECT id, username, email, password_hash, role, created_at
        FROM users WHERE username = $1 LIMIT 1
    """
    user_row = await DatabasePool.fetch_one(q, username)
    
    if not user_row:
        logger.warning(f"Login attempt with non-existent user: {username}")
        return None
    
    # Verifica senha
    is_valid = await verify_password(password, user_row["password_hash"])
    if not is_valid:
        logger.warning(f"Failed login attempt for user: {username}")
        return None
    
    logger.info(f"Successful login for user: {username}")
    return user_row

def create_access_token(user_id: str, username: str, role: str) -> TokenResponse:
    """
    Cria JWT com payload contenho user_id e role.
    Expiração: configurável via env (padrão: 15 minutos).
    """
    expiration_hours = settings.jwt_expiration_hours
    expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)
    exp_timestamp = int(expires_at.timestamp())
    
    payload = {
        "user_id": str(user_id),
        "username": username,
        "role": role,
        "exp": exp_timestamp,
    }
    
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    
    expires_in = int((expires_at - datetime.utcnow()).total_seconds())
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user_id=user_id,
        role=role,
    )

def decode_token(token: str) -> Optional[TokenPayload]:
    """
    Decodifica e valida JWT.
    Retorna payload se válido, None se inválido ou expirado.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token inválido: {str(e)}")
        return None