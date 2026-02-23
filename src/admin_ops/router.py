from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional, List

from src.admin_ops.schemas import (
    CreateFolderRequest,
    CreateFileRequest,
    RenameFolderRequest,
    RenameFileRequest,
    MoveNodeRequest,
    AdminOperationResponse,
    AdminNodeOut,
)
from src.admin_ops import service
from src.authorization import require_admin
from src.auth.schemas import TokenPayload
from src.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/folders", response_model=AdminNodeOut, status_code=status.HTTP_201_CREATED)
async def create_folder(
    payload: CreateFolderRequest,
    current_user: TokenPayload = Depends(require_admin()),
):
    """
    Cria pasta (admin only).
    """
    try:
        node = await service.create_folder(
            current_user,
            payload.name,
            payload.parent_id
        )
        return AdminNodeOut(**node.dict())
    except PermissionError:
        raise HTTPException(status_code=403, detail="admin_access_required")
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "parent_not_found":
            raise HTTPException(status_code=404, detail="parent_not_found")
        elif error_msg == "parent_must_be_folder":
            raise HTTPException(status_code=400, detail="parent_must_be_folder")
        elif error_msg == "name_already_exists_in_parent":
            raise HTTPException(status_code=400, detail="name_already_exists_in_parent")
        elif error_msg == "folder_name_empty":
            raise HTTPException(status_code=400, detail="folder_name_empty")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creating folder", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.post("/files", response_model=AdminNodeOut, status_code=status.HTTP_201_CREATED)
async def create_file(
    payload: CreateFileRequest,
    current_user: TokenPayload = Depends(require_admin()),
):
    """
    Cria arquivo .txt (admin only).
    Opcionalmente inicializa com conteúdo.
    """
    try:
        node = await service.create_file(
            current_user,
            payload.name,
            payload.parent_id,
            payload.initial_content or ""
        )
        return AdminNodeOut(**node.dict())
    except PermissionError:
        raise HTTPException(status_code=403, detail="admin_access_required")
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "parent_not_found":
            raise HTTPException(status_code=404, detail="parent_not_found")
        elif error_msg == "parent_must_be_folder":
            raise HTTPException(status_code=400, detail="parent_must_be_folder")
        elif error_msg == "name_already_exists_in_parent":
            raise HTTPException(status_code=400, detail="name_already_exists_in_parent")
        elif error_msg == "file_name_empty":
            raise HTTPException(status_code=400, detail="file_name_empty")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creating file", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.patch("/{node_id}/rename", response_model=AdminNodeOut)
async def rename_node(
    node_id: str,
    payload: RenameFolderRequest,
    current_user: TokenPayload = Depends(require_admin()),
):
    """
    Renomeia node (pasta ou arquivo).
    Admin only.
    """
    try:
        node = await service.rename_node(current_user, node_id, payload.new_name)
        return AdminNodeOut(**node.dict())
    except PermissionError:
        raise HTTPException(status_code=403, detail="admin_access_required")
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "node_not_found":
            raise HTTPException(status_code=404, detail="node_not_found")
        elif error_msg == "new_name_empty":
            raise HTTPException(status_code=400, detail="new_name_empty")
        elif error_msg == "name_already_exists_in_parent":
            raise HTTPException(status_code=400, detail="name_already_exists_in_parent")
        elif error_msg == "cyclic_move_not_allowed":
            raise HTTPException(status_code=400, detail="cyclic_move_not_allowed")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error renaming node", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.patch("/{node_id}/move", response_model=AdminNodeOut)
async def move_node(
    node_id: str,
    payload: MoveNodeRequest,
    current_user: TokenPayload = Depends(require_admin()),
):
    """
    Move node para outro parent.
    Admin only.
    Valida ciclos automaticamente.
    """
    try:
        node = await service.move_node(current_user, node_id, payload.new_parent_id)
        return AdminNodeOut(**node.dict())
    except PermissionError:
        raise HTTPException(status_code=403, detail="admin_access_required")
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "node_not_found":
            raise HTTPException(status_code=404, detail="node_not_found")
        elif error_msg == "cannot_move_root":
            raise HTTPException(status_code=400, detail="cannot_move_root")
        elif error_msg == "cyclic_move_not_allowed":
            raise HTTPException(status_code=400, detail="cyclic_move_not_allowed")
        elif error_msg == "parent_not_found":
            raise HTTPException(status_code=404, detail="parent_not_found")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error moving node", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.delete("/{node_id}", response_model=AdminOperationResponse)
async def delete_node(
    node_id: str,
    current_user: TokenPayload = Depends(require_admin()),
):
    """
    Deleta node e toda sua subárvore (cascade).
    Admin only.
    Retorna informações sobre o node deletado.
    """
    try:
        result = await service.delete_node(current_user, node_id)
        return AdminOperationResponse(
            success=result["success"],
            message=result["message"],
            node_id=result["node_id"],
            node_type=result["node_type"],
            operation="delete",
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="admin_access_required")
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "node_not_found":
            raise HTTPException(status_code=404, detail="node_not_found")
        elif error_msg == "cannot_delete_root":
            raise HTTPException(status_code=400, detail="cannot_delete_root")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error deleting node", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.post("/bulk-delete", response_model=dict)
async def bulk_delete(
    node_ids: List[str],
    current_user: TokenPayload = Depends(require_admin()),
):
    """
    Deleta múltiplos nodes em massa.
    Admin only.
    Retorna summary de sucesso/falha para cada node.
    """
    try:
        result = await service.bulk_delete_nodes(current_user, node_ids)
        return result
    except PermissionError:
        raise HTTPException(status_code=403, detail="admin_access_required")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error bulk deleting nodes", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.get("/summary", response_model=dict)
async def get_system_summary(
    current_user: TokenPayload = Depends(require_admin()),
):
    """
    Retorna resumo do sistema (dashboard admin).
    Admin only.
    """
    try:
        summary = await service.get_admin_summary()
        return summary
    except Exception as e:
        logger.error("Error getting admin summary", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")