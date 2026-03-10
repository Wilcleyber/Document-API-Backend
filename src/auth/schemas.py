from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List, Union, Union
from uuid import UUID

class LoginRequest(BaseModel):
    """Payload de login."""
    username: str
    password: str

class TokenResponse(BaseModel):
    """Resposta com token JWT."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos
    user_id: Union[UUID, str] # Usando Union ou | conforme sua versão do Python
    role: str

    model_config = ConfigDict(from_attributes=True)

class TokenPayload(BaseModel):
    """Payload decodificado do JWT."""
    user_id: Union[UUID, str] # Ajustado para não dar erro na decodificação
    username: str
    role: str
    exp: int  