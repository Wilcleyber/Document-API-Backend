from typing import Optional, List, Union
from uuid import UUID
from src.auth.schemas import TokenPayload
from src.nodes.schemas import NodeCreate, NodeUpdate, NodeOut
from src.nodes import service as node_service
from src.file_content import service as content_service
from src.core.logging_config import get_logger

logger = get_logger(__name__)

def _ensure_admin(user: TokenPayload) -> None:
    """Valida que user é ADMIN. Levanta ValueError se não."""
    if user.role != "ADMIN":
        logger.warning(f"Non-admin attempted admin operation: {user.user_id}")
        raise PermissionError("admin_access_required")

async def create_folder(user: TokenPayload, folder_name: str, parent_id: Optional[str] = None) -> NodeOut:
    """
    Cria pasta sob supervisão admin.
    Encapsula create_node com validações extras.
    """
    _ensure_admin(user)
    
    if not folder_name or not folder_name.strip():
        raise ValueError("folder_name_empty")
    
    payload = NodeCreate(
        name=folder_name.strip(),
        type="FOLDER",
        parent_id=parent_id
    )
    
    try:
        node = await node_service.create_node(payload)
        logger.info(
            f"Folder created by admin: {node.id}",
            extra={"admin_id": user.user_id, "parent_id": parent_id}
        )
        return node
    except ValueError as e:
        logger.warning(f"Folder creation failed: {str(e)}")
        raise

async def create_file(
    user: TokenPayload,
    file_name: str,
    parent_id: Optional[str] = None,
    initial_content: str = ""
) -> NodeOut:
    """
    Cria arquivo .txt sob supervisão admin.
    Encapsula create_node + save_file_content.
    """
    _ensure_admin(user)
    
    if not file_name or not file_name.strip():
        raise ValueError("file_name_empty")
    
    # Garante extensão .txt
    file_name = file_name.strip()
    if not file_name.endswith(".txt"):
        file_name += ".txt"
    
    payload = NodeCreate(
        name=file_name,
        type="FILE",
        parent_id=parent_id
    )
    
    try:
        node = await node_service.create_node(payload)
        
        # Salva conteúdo inicial (se fornecido)
        if initial_content:
            await content_service.save_file_content(node.id, initial_content, user_id=user.user_id)
        
        logger.info(
            f"File created by admin: {node.id}",
            extra={"admin_id": user.user_id, "parent_id": parent_id, "content_length": len(initial_content)}
        )
        return node
    except ValueError as e:
        logger.warning(f"File creation failed: {str(e)}")
        raise

async def rename_node(
    user: TokenPayload,
    node_id: Union[UUID, str],
    new_name: str
) -> NodeOut:
    """
    Renomeia node (pasta ou arquivo).
    Encapsula update_node com validação de nome.
    """
    _ensure_admin(user)
    
    if not new_name or not new_name.strip():
        raise ValueError("new_name_empty")
    
    node = await node_service.get_node_by_id(node_id)
    if not node:
        raise ValueError("node_not_found")
    
    new_name = new_name.strip()
    
    # Se é arquivo, garante .txt
    if node.type == "FILE" and not new_name.endswith(".txt"):
        new_name += ".txt"
    
    payload = NodeUpdate(name=new_name)
    
    try:
        updated = await node_service.update_node(node_id, payload)
        logger.info(
            f"Node renamed by admin: {node_id}",
            extra={"admin_id": user.user_id, "old_name": node.name, "new_name": new_name}
        )
        return updated
    except ValueError as e:
        logger.warning(f"Rename failed: {str(e)}")
        raise

async def move_node(
    user: TokenPayload,
    node_id: Union[UUID, str],
    new_parent_id: Optional[str] = None
) -> NodeOut:
    """
    Move node para outro parent.
    Encapsula update_node com validação de ciclo.
    """
    _ensure_admin(user)
    
    node = await node_service.get_node_by_id(node_id)
    if not node:
        raise ValueError("node_not_found")
    
    # Impede mover a raiz
    if node.parent_id is None and new_parent_id is None:
        raise ValueError("cannot_move_root")
    
    payload = NodeUpdate(parent_id=new_parent_id)
    
    try:
        updated = await node_service.update_node(node_id, payload)
        logger.info(
            f"Node moved by admin: {node_id}",
            extra={"admin_id": user.user_id, "old_parent": node.parent_id, "new_parent": new_parent_id}
        )
        return updated
    except ValueError as e:
        logger.warning(f"Move failed: {str(e)}")
        raise

async def delete_node(user: TokenPayload, node_id: Union[UUID, str]) -> dict:
    """
    Deleta node e toda sua subárvore (cascade).
    Requer confirmação de role ADMIN.
    """
    _ensure_admin(user)
    
    node = await node_service.get_node_by_id(node_id)
    if not node:
        raise ValueError("node_not_found")
    
    # Impede deletar a raiz (nodes sem parent_id)
    if node.parent_id is None:
        raise ValueError("cannot_delete_root")
    
    try:
        await node_service.delete_node(node_id)
        logger.info(
            f"Node deleted by admin (cascade): {node_id}",
            extra={"admin_id": user.user_id, "node_type": node.type, "node_name": node.name}
        )
        return {
            "success": True,
            "message": f"Node '{node.name}' and all descendants deleted",
            "node_id": node_id,
            "node_type": node.type,
        }
    except ValueError as e:
        logger.warning(f"Delete failed: {str(e)}")
        raise

async def bulk_delete_nodes(user: TokenPayload, node_ids: list[str]) -> dict:
    """
    Deleta múltiplos nodes (útil para limpeza em massa).
    """
    _ensure_admin(user)
    
    if not node_ids:
        raise ValueError("no_nodes_to_delete")
    
    deleted = []
    failed = []
    
    for node_id in node_ids:
        try:
            await delete_node(user, node_id)
            deleted.append(node_id)
        except (ValueError, PermissionError) as e:
            failed.append({"node_id": node_id, "error": str(e)})
    
    logger.info(
        f"Bulk delete by admin: {len(deleted)} deleted, {len(failed)} failed",
        extra={"admin_id": user.user_id}
    )
    
    return {
        "success": len(failed) == 0,
        "message": f"Deleted {len(deleted)} nodes, {len(failed)} failed",
        "deleted": deleted,
        "failed": failed,
    }

async def get_admin_summary() -> dict:
    """
    Retorna resumo do sistema (para dashboard admin).
    """
    from src.db.connection import DatabasePool
    
    stats_q = """
    SELECT 
        (SELECT COUNT(*) FROM items) as total_nodes,
        (SELECT COUNT(*) FROM items WHERE type = 'FOLDER') as total_folders,
        (SELECT COUNT(*) FROM items WHERE type = 'FILE') as total_files,
        (SELECT COUNT(*) FROM file_contents) as files_with_content,
        (SELECT COUNT(*) FROM users) as total_users,
        (SELECT COUNT(*) FROM users WHERE role = 'ADMIN') as admin_users
    """
    
    result = await DatabasePool.fetch_one(stats_q)
    
    return {
        "total_nodes": result["total_nodes"] or 0,
        "total_folders": result["total_folders"] or 0,
        "total_files": result["total_files"] or 0,
        "files_with_content": result["files_with_content"] or 0,
        "total_users": result["total_users"] or 0,
        "admin_users": result["admin_users"] or 0,
    }