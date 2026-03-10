from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

class BreadcrumbItem(BaseModel):
    """Item no breadcrumb."""
    id: Union[UUID, str]
    name: str
    type: str

class PathResponse(BaseModel):
    """Resposta com caminho completo (breadcrumb)."""
    path: List[BreadcrumbItem]
    full_path: str  # Ex: "Home > Documentos > Faculdade"

class TreeNode(BaseModel):
    """Node com children para listagem recursiva."""
    id: Union[UUID, str]
    name: str
    type: str
    parent_id: Optional[Union[UUID, str]]
    created_at: datetime
    updated_at: datetime
    children: List["TreeNode"] = []

    model_config = ConfigDict(from_attributes=True)

TreeNode.model_rebuild()

class SearchResult(BaseModel):
    """Resultado de busca com caminho completo."""
    id: Union[UUID, str]
    name: str
    type: str
    path: str  # Ex: "Home > Documentos"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedSearchResults(BaseModel):
    """Resultados paginados de busca."""
    total: int
    page: int
    per_page: int
    results: List[SearchResult]