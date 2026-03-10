from typing import Optional, List, Union
from uuid import UUID
from src.db.connection import DatabasePool
from src.db.transactions import TransactionManager
from src.nodes.schemas import NodeCreate, NodeUpdate, NodeOut
from src.core.logging_config import get_logger

logger = get_logger(__name__)

async def create_node(payload: NodeCreate) -> NodeOut:
    """
    Cria novo node (FOLDER ou FILE).
    Valida parent_id se fornecido.
    """
    # Valida parent_id se fornecido
    if payload.parent_id:
        parent = await get_node_by_id(payload.parent_id)
        if not parent:
            raise ValueError("parent_not_found")
        if parent.type != "FOLDER":
            raise ValueError("parent_must_be_folder")
    
    # Verifica unicidade de nome dentro do mesmo parent_id
    duplicate_q = """
        SELECT id FROM items 
        WHERE parent_id IS NOT DISTINCT FROM $1 AND name = $2 AND type = $3
        LIMIT 1
    """
    dup = await DatabasePool.fetch_one(
        duplicate_q,
        payload.parent_id,
        payload.name,
        payload.type
    )
    if dup:
        raise ValueError("name_already_exists_in_parent")
    
    insert_q = """
        INSERT INTO items (id, parent_id, type, name, created_at, updated_at)
        VALUES (gen_random_uuid(), $1, $2, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING id, parent_id, type, name, created_at, updated_at
    """
    row = await DatabasePool.fetch_one(
        insert_q,
        payload.parent_id,
        payload.type,
        payload.name
    )
    
    logger.info(f"Node created: {row['id']} (type={payload.type}, name={payload.name})")
    return NodeOut(**row)

async def get_node_by_id(node_id: Union[UUID, str]) -> Optional[NodeOut]:
    """Retorna um node por ID."""
    q = """
        SELECT id, parent_id, type, name, created_at, updated_at
        FROM items WHERE id = $1
    """
    row = await DatabasePool.fetch_one(q, node_id)
    return NodeOut(**row) if row else None

async def list_children(parent_id: Optional[str] = None) -> List[NodeOut]:
    """
    Lista filhos diretos de um parent.
    Se parent_id é None, retorna raiz.
    """
    q = """
        SELECT id, parent_id, type, name, created_at, updated_at
        FROM items WHERE parent_id IS NOT DISTINCT FROM $1
        ORDER BY type DESC, name ASC
    """
    rows = await DatabasePool.fetch_all(q, parent_id)
    return [NodeOut(**row) for row in rows]

async def list_root() -> List[NodeOut]:
    """Lista nodes na raiz (parent_id IS NULL)."""
    return await list_children(parent_id=None)

async def _get_descendants(node_id: Union[UUID, str]) -> List[str]:
    """
    Query recursiva que retorna IDs de todos os descendentes.
    Usado para validar ciclos e delete_cascade.
    """
    q = """
        WITH RECURSIVE descendants AS (
            SELECT id FROM items WHERE id = $1
            UNION
            SELECT i.id FROM items i
            JOIN descendants d ON i.parent_id = d.id
        )
        SELECT id FROM descendants
    """
    rows = await DatabasePool.fetch_all(q, node_id)
    return [row["id"] for row in rows]

async def _validate_move(node_id: Union[UUID, str], new_parent_id: Optional[str]) -> bool:
    """
    Valida se é seguro mover node_id para new_parent_id.
    Retorna False se causaria ciclo (new_parent é descendente de node).
    """
    if new_parent_id is None:
        # Mover para raiz é sempre segurado
        return True
    
    # Busca todos os descendentes de node_id
    descendants = await _get_descendants(node_id)
    
    # Se new_parent_id está em descendants, é ciclo
    if new_parent_id in descendants:
        return False
    
    return True

async def update_node(node_id: Union[UUID, str], payload: NodeUpdate) -> NodeOut:
    """
    Atualiza node (rename e/ou move).
    Valida ciclos antes de mover.
    """
    node = await get_node_by_id(node_id)
    if not node:
        raise ValueError("node_not_found")
    
    # Prepare updated values
    new_name = payload.name if payload.name is not None else node.name
    new_parent_id = payload.parent_id if payload.parent_id is not None else node.parent_id
    
    # Se tentando mover
    if payload.parent_id is not None and payload.parent_id != node.parent_id:
        # Valida ciclo
        if not await _validate_move(node_id, payload.parent_id):
            raise ValueError("cyclic_move_not_allowed")
        
        # Valida parent existe
        if payload.parent_id:
            parent = await get_node_by_id(payload.parent_id)
            if not parent:
                raise ValueError("parent_not_found")
            if parent.type != "FOLDER":
                raise ValueError("parent_must_be_folder")
    
    # Se renomeando, verifica duplicata no mesmo parent
    if payload.name is not None and payload.name != node.name:
        duplicate_q = """
            SELECT id FROM items 
            WHERE parent_id IS NOT DISTINCT FROM $1 AND name = $2 AND id != $3 AND type = $4
            LIMIT 1
        """
        dup = await DatabasePool.fetch_one(
            duplicate_q,
            new_parent_id,
            new_name,
            node_id,
            node.type
        )
        if dup:
            raise ValueError("name_already_exists_in_parent")
    
    update_q = """
        UPDATE items
        SET name = $1, parent_id = $2, updated_at = CURRENT_TIMESTAMP
        WHERE id = $3
        RETURNING id, parent_id, type, name, created_at, updated_at
    """
    row = await DatabasePool.fetch_one(update_q, new_name, new_parent_id, node_id)
    
    logger.info(f"Node updated: {node_id} (name={new_name}, parent_id={new_parent_id})")
    return NodeOut(**row)

async def delete_node(node_id: Union[UUID, str]) -> None:
    """
    Deleta node e todos seus descendentes (cascata).
    """
    node = await get_node_by_id(node_id)
    if not node:
        raise ValueError("node_not_found")
    
    # Usa transaction para delete cascata
    async with TransactionManager.transaction() as conn:
        q = """
            WITH RECURSIVE descendants AS (
                SELECT id FROM items WHERE id = $1
                UNION
                SELECT i.id FROM items i
                JOIN descendants d ON i.parent_id = d.id
            )
            DELETE FROM items WHERE id IN (SELECT id FROM descendants)
        """
        await conn.execute(q, node_id)
    
    logger.info(f"Node deleted: {node_id} (cascade delete)")

async def get_tree(parent_id: Optional[str] = None) -> dict:
    """
    Retorna árvore completa a partir de um parent.
    Estrutura recursiva com children.
    """
    q = """
        WITH RECURSIVE tree AS (
            SELECT id, parent_id, type, name, created_at, updated_at, CAST(id AS VARCHAR) AS path
            FROM items WHERE parent_id IS NOT DISTINCT FROM $1
            UNION
            SELECT i.id, i.parent_id, i.type, i.name, i.created_at, i.updated_at, 
                   CONCAT(t.path, '/', i.id)
            FROM items i
            JOIN tree t ON i.parent_id = t.id
        )
        SELECT id, parent_id, type, name, created_at, updated_at
        FROM tree ORDER BY parent_id, name
    """
    rows = await DatabasePool.fetch_all(q, parent_id)
    
    # Constrói estrutura hierárquica
    nodes_map = {row["id"]: {"data": NodeOut(**row), "children": []} for row in rows}
    
    root_node = None
    for node_id, node_info in nodes_map.items():
        parent_id_val = node_info["data"].parent_id
        if parent_id_val is None:
            root_node = node_info
        elif parent_id_val in nodes_map:
            nodes_map[parent_id_val]["children"].append(node_info)
    
    return root_node if root_node else {"data": None, "children": []}