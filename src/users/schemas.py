from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserOut(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DemoCredentials(BaseModel):
    username: str
    email: EmailStr
    password: str