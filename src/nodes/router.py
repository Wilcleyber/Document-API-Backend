from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional, List, Union
from uuid import UUID
from src.nodes.schemas import NodeCreate, NodeUpdate, NodeOut
from src.nodes import service
from src.authorization import require_manage_node, require_admin
from src.auth.dependencies import get_current_user
from src.auth.schemas import TokenPayload
from src.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/items", tags=["items"])

@router.post("", response_model=NodeOut, status_code=status.HTTP_201_CREATED)
async def create_node(
    payload: NodeCreate,
    current_user: TokenPayload = Depends(require_manage_node()),
):
    """
    Cria novo node (FOLDER ou FILE).
    Apenas ADMIN pode criar.
    """
    try:
        node = await service.create_node(payload)
        return node
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "parent_not_found":
            raise HTTPException(status_code=404, detail="parent_not_found")
        elif error_msg == "parent_must_be_folder":
            raise HTTPException(status_code=400, detail="parent_must_be_folder")
        elif error_msg == "name_already_exists_in_parent":
            raise HTTPException(status_code=400, detail="name_already_exists_in_parent")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating node: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.get("/{node_id}", response_model=NodeOut)
async def get_node(
    node_id: Union[UUID, str],
    current_user: TokenPayload = Depends(get_current_user),
):
    """Retorna dados de um node."""
    node = await service.get_node_by_id(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="node_not_found")
    return node

@router.get("/{node_id}/children", response_model=List[NodeOut])
async def list_node_children(
    node_id: Union[UUID, str],
    current_user: TokenPayload = Depends(get_current_user),
):
    """Lista filhos diretos de um node."""
    node = await service.get_node_by_id(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="node_not_found")
    
    children = await service.list_children(node_id)
    return children

@router.get("", response_model=List[NodeOut])
async def list_nodes(
    parent_id: Optional[str] = None,
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Lista nodes em um diretório.
    Se parent_id=null, retorna raiz.
    """
    if parent_id is None:
        nodes = await service.list_root()
    else:
        # Valida parent existe
        parent = await service.get_node_by_id(parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="parent_not_found")
        nodes = await service.list_children(parent_id)
    
    return nodes

@router.get("/root", response_model=List[NodeOut])
async def list_root_nodes(
    current_user: TokenPayload = Depends(get_current_user),
):
    """Lista nodes na raiz."""
    nodes = await service.list_root()
    return nodes

@router.patch("/{node_id}", response_model=NodeOut)
async def update_node(
    node_id: Union[UUID, str],
    payload: NodeUpdate,
    current_user: TokenPayload = Depends(require_manage_node()),
):
    """
    Atualiza node (rename e/ou move).
    Apenas ADMIN pode atualizar.
    Valida ciclos antes de mover.
    """
    try:
        node = await service.update_node(node_id, payload)
        return node
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "node_not_found":
            raise HTTPException(status_code=404, detail="node_not_found")
        elif error_msg == "cyclic_move_not_allowed":
            raise HTTPException(status_code=400, detail="cyclic_move_not_allowed")
        elif error_msg == "parent_not_found":
            raise HTTPException(status_code=404, detail="parent_not_found")
        elif error_msg == "parent_must_be_folder":
            raise HTTPException(status_code=400, detail="parent_must_be_folder")
        elif error_msg == "name_already_exists_in_parent":
            raise HTTPException(status_code=400, detail="name_already_exists_in_parent")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating node: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: Union[UUID, str],
    current_user: TokenPayload = Depends(require_manage_node()),
):
    """
    Deleta node e toda sua subárvore.
    Apenas ADMIN pode deletar.
    """
    try:
        await service.delete_node(node_id)
        return None
    except ValueError as e:
        if str(e) == "node_not_found":
            raise HTTPException(status_code=404, detail="node_not_found")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting node: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.get("/tree/full", response_model=dict)
async def get_full_tree(
    current_user: TokenPayload = Depends(get_current_user),
):
    """Retorna árvore completa de nodes."""
    try:
        tree = await service.get_tree(parent_id=None)
        return tree
    except Exception as e:
        logger.error(f"Error fetching tree: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")