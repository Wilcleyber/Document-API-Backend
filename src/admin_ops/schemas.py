from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Union, Union
from uuid import UUID

class CreateFolderRequest(BaseModel):
    """Request para criar pasta."""
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[Union[UUID, str]] = None

class CreateFileRequest(BaseModel):
    """Request para criar arquivo."""
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[Union[UUID, str]] = None
    initial_content: Optional[str] = ""

class RenameFolderRequest(BaseModel):
    """Request para renomear pasta."""
    new_name: str = Field(..., min_length=1, max_length=255)

class RenameFileRequest(BaseModel):
    """Request para renomear arquivo."""
    new_name: str = Field(..., min_length=1, max_length=255)

class MoveNodeRequest(BaseModel):
    """Request para mover node."""
    new_parent_id: Optional[Union[UUID, str]] = None

class AdminOperationResponse(BaseModel):
    """Response genérica de operação admin."""
    success: bool
    message: str
    node_id: Optional[Union[UUID, str]] = None
    node_type: Optional[str] = None
    operation: str

class AdminNodeOut(BaseModel):
    """Node retornado após operação admin."""
    id: Union[UUID, str]
    name: str
    type: str
    parent_id: Optional[Union[UUID, str]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)