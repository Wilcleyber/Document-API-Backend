from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class BreadcrumbItem(BaseModel):
    """Item no breadcrumb."""
    id: str
    name: str
    type: str

class PathResponse(BaseModel):
    """Resposta com caminho completo (breadcrumb)."""
    path: List[BreadcrumbItem]
    full_path: str  # Ex: "Home > Documentos > Faculdade"

class TreeNode(BaseModel):
    """Node com children para listagem recursiva."""
    id: str
    name: str
    type: str
    parent_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    children: List["TreeNode"] = []

TreeNode.update_forward_refs()

class SearchResult(BaseModel):
    """Resultado de busca com caminho completo."""
    id: str
    name: str
    type: str
    path: str  # Ex: "Home > Documentos"
    created_at: datetime
    updated_at: datetime

class PaginatedSearchResults(BaseModel):
    """Resultados paginados de busca."""
    total: int
    page: int
    per_page: int
    results: List[SearchResult]