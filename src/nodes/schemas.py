from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Union, Union, List
from uuid import UUID

class NodeCreate(BaseModel):
    """Payload para criar node (FOLDER ou FILE)."""
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern="^(FOLDER|FILE)$")
    parent_id: Optional[Union[UUID, str]] = None

class NodeUpdate(BaseModel):
    """Payload para atualizar node (rename/move)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[Union[UUID, str]] = None

class NodeOut(BaseModel):
    """Response com dados do node."""
    id: Union[UUID, str]
    parent_id: Optional[str]
    type: str
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NodeTree(NodeOut):
    """Node com children (para listagem recursiva)."""
    children: list["NodeTree"] = Field(default_factory=list)

NodeTree.model_rebuild()
