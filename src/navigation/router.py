from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from src.navigation.schemas import (
    PathResponse,
    TreeNode,
    PaginatedSearchResults,
)
from src.navigation import service
from src.auth.dependencies import get_current_user
from src.auth.schemas import TokenPayload
from src.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/navigation", tags=["navigation"])

@router.get("/{node_id}/path", response_model=PathResponse)
async def get_breadcrumb(
    node_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Retorna breadcrumb (caminho completo) de um node até a raiz.
    Ex: [Home, Documentos, Faculdade]
    """
    try:
        path = await service.get_path(node_id)
        return path
    except ValueError as e:
        if str(e) == "node_not_found":
            raise HTTPException(status_code=404, detail="node_not_found")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting breadcrumb: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.get("/{node_id}/tree", response_model=TreeNode)
async def get_tree_recursive(
    node_id: str,
    depth: int = Query(10, ge=1, le=20),
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Retorna árvore recursiva até N níveis (default 10, máx 20).
    """
    try:
        tree = await service.list_recursive(node_id, max_depth=depth)
        return tree
    except ValueError as e:
        if str(e) == "node_not_found":
            raise HTTPException(status_code=404, detail="node_not_found")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting tree: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.get("/search", response_model=PaginatedSearchResults)
async def search_nodes(
    q: str = Query(..., min_length=1, max_length=255),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None, pattern="^(FOLDER|FILE)$"),
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Busca nodes por nome com paginação.
    
    - **q**: termo de busca (case-insensitive)
    - **page**: página (padrão: 1)
    - **per_page**: itens por página (padrão: 20, máx: 100)
    - **type**: filtro por tipo (FOLDER ou FILE, opcional)
    """
    try:
        results = await service.search(q, page=page, per_page=per_page, node_type=type)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching nodes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.get("/{node_id}/siblings", response_model=list)
async def get_siblings(
    node_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Retorna irmãos (nodes com mesmo parent_id).
    """
    try:
        siblings = await service.get_siblings(node_id)
        return siblings
    except ValueError as e:
        if str(e) == "node_not_found":
            raise HTTPException(status_code=404, detail="node_not_found")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting siblings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.get("/{node_id}/stats", response_model=dict)
async def get_stats(
    node_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Retorna estatísticas de um diretório:
    total files, total folders, total descendants.
    """
    try:
        stats = await service.get_directory_stats(node_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.get("/{node_id}/path-string")
async def get_path_string(
    node_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Retorna caminho completo como string simples.
    Ex: "Home > Documentos > Faculdade"
    """
    try:
        path_str = await service.get_full_path_string(node_id)
        return {"path": path_str}
    except ValueError as e:
        if str(e) == "node_not_found":
            raise HTTPException(status_code=404, detail="node_not_found")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting path string: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")