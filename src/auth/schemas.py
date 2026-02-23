from pydantic import BaseModel, EmailStr
from datetime import datetime

class LoginRequest(BaseModel):
    """Payload de login."""
    username: str
    password: str

class TokenResponse(BaseModel):
    """Resposta com token JWT."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos
    user_id: str
    role: str

class TokenPayload(BaseModel):
    """Payload decodificado do JWT."""
    user_id: str
    username: str
    role: str
    exp: int  # Unix timestamp de expiração