from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class NodeCreate(BaseModel):
    """Payload para criar node (FOLDER ou FILE)."""
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern="^(FOLDER|FILE)$")
    parent_id: Optional[str] = None

class NodeUpdate(BaseModel):
    """Payload para atualizar node (rename/move)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[str] = None

class NodeOut(BaseModel):
    """Response com dados do node."""
    id: str
    parent_id: Optional[str]
    type: str
    name: str
    created_at: datetime
    updated_at: datetime

class NodeTree(NodeOut):
    """Node com children (para listagem recursiva)."""
    children: list["NodeTree"] = Field(default_factory=list)

NodeTree.model_rebuild()
