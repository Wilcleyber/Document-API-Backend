from typing import List, Optional, Dict
from src.db.connection import DatabasePool
from src.navigation.schemas import (
    BreadcrumbItem,
    PathResponse,
    TreeNode,
    SearchResult,
    PaginatedSearchResults,
)
from src.core.logging_config import get_logger

logger = get_logger(__name__)

async def get_path(node_id: Union[UUID, str]) -> PathResponse:
    """
    Retorna breadcrumb (caminho completo) de um node até a raiz.
    Query única com CTE recursiva (ancestors).
    """
    q = """
        WITH RECURSIVE ancestors AS (
            SELECT id, name, type, parent_id FROM items WHERE id = $1
            UNION
            SELECT i.id, i.name, i.type, i.parent_id
            FROM items i
            JOIN ancestors a ON i.id = a.parent_id
        )
        SELECT id, name, type FROM ancestors ORDER BY parent_id DESC
    """
    rows = await DatabasePool.fetch_all(q, node_id)
    
    if not rows:
        raise ValueError("node_not_found")
    
    # Constrói breadcrumb (raiz para node)
    breadcrumb = [BreadcrumbItem(**row) for row in reversed(rows)]
    
    # Constrói full_path string
    full_path = " > ".join([item.name for item in breadcrumb])
    
    return PathResponse(path=breadcrumb, full_path=full_path)

async def list_recursive(node_id: Union[UUID, str], max_depth: int = 10) -> TreeNode:
    """
    Lista árvore recursiva até max_depth níveis.
    Retorna estrutura hierárquica completa.
    """
    # Valida node existe
    node_q = "SELECT id, name, type, parent_id, created_at, updated_at FROM items WHERE id = $1"
    node_row = await DatabasePool.fetch_one(node_q, node_id)
    if not node_row:
        raise ValueError("node_not_found")
    
    # Busca todos descentes com level
    q = """
        WITH RECURSIVE tree AS (
            SELECT id, name, type, parent_id, created_at, updated_at, 1 as level
            FROM items WHERE parent_id = $1
            UNION ALL
            SELECT i.id, i.name, i.type, i.parent_id, i.created_at, i.updated_at, t.level + 1
            FROM items i
            JOIN tree t ON i.parent_id = t.id
            WHERE t.level < $2
        )
        SELECT id, name, type, parent_id, created_at, updated_at, level
        FROM tree ORDER BY parent_id, name
    """
    rows = await DatabasePool.fetch_all(q, node_id, max_depth)
    
    # Constrói estrutura hierárquica
    nodes_map = {
        row["id"]: TreeNode(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            parent_id=row["parent_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            children=[]
        )
        for row in rows
    }
    
    # Monta árvore
    root = TreeNode(
        id=node_row["id"],
        name=node_row["name"],
        type=node_row["type"],
        parent_id=node_row["parent_id"],
        created_at=node_row["created_at"],
        updated_at=node_row["updated_at"],
        children=[]
    )
    
    for node_id_key, node in nodes_map.items():
        if node.parent_id == root.id:
            root.children.append(node)
    
    for node_id_key, node in nodes_map.items():
        for child in nodes_map.values():
            if child.parent_id == node_id_key:
                node.children.append(child)
    
    return root

async def search(
    query: str,
    page: int = 1,
    per_page: int = 20,
    node_type: Optional[str] = None,
) -> PaginatedSearchResults:
    """
    Busca nodes por nome com paginação.
    Retorna caminho completo para cada resultado.
    """
    if page < 1 or per_page < 1:
        raise ValueError("invalid_pagination")
    
    offset = (page - 1) * per_page
    
    # Count total
    count_q = """
        SELECT COUNT(*) as total FROM items
        WHERE name ILIKE $1
    """
    count_args = [f"%{query}%"]
    
    if node_type:
        count_q += " AND type = $2"
        count_args.append(node_type)
    
    count_result = await DatabasePool.fetch_one(count_q, *count_args)
    total = count_result["total"] if count_result else 0
    
    # Search com paginação
    search_q = """
        WITH ancestors AS (
            SELECT 
                i.id, i.name, i.type, i.created_at, i.updated_at,
                STRING_AGG(a.name, ' > ' ORDER BY a.depth DESC) as path_str
            FROM items i
            LEFT JOIN LATERAL (
                WITH RECURSIVE anc AS (
                    SELECT id, name, parent_id, 1 as depth
                    FROM items WHERE id = i.parent_id
                    UNION
                    SELECT a.id, a.name, a.parent_id, anc.depth + 1
                    FROM items a
                    JOIN anc ON a.id = anc.parent_id
                )
                SELECT name, depth FROM anc
            ) a ON TRUE
            WHERE i.name ILIKE $1
    """
    
    search_args = [f"%{query}%"]
    param_count = 2
    
    if node_type:
        search_q += f" AND i.type = ${param_count}"
        search_args.append(node_type)
        param_count += 1
    
    search_q += f"""
            GROUP BY i.id, i.name, i.type, i.created_at, i.updated_at
            ORDER BY i.name ASC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        )
        SELECT id, name, type, created_at, updated_at, 
               COALESCE(path_str, '') as path_str
        FROM ancestors
    """
    
    search_args.extend([per_page, offset])
    
    rows = await DatabasePool.fetch_all(search_q, *search_args)
    
    results = [
        SearchResult(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            path=row["path_str"] or "[raiz]",
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]
    
    return PaginatedSearchResults(
        total=total,
        page=page,
        per_page=per_page,
        results=results,
    )

async def get_full_path_string(node_id: Union[UUID, str]) -> str:
    """
    Retorna apenas a string do caminho completo.
    Ex: "Home > Documentos > Faculdade"
    """
    path_response = await get_path(node_id)
    return path_response.full_path

async def get_siblings(node_id: Union[UUID, str]) -> List[Dict]:
    """
    Retorna os irmãos (nodes com mesmo parent_id).
    """
    # Busca parent_id
    q = "SELECT parent_id FROM items WHERE id = $1"
    node_row = await DatabasePool.fetch_one(q, node_id)
    
    if not node_row:
        raise ValueError("node_not_found")
    
    parent_id = node_row["parent_id"]
    
    # Busca siblings
    siblings_q = """
        SELECT id, name, type, created_at, updated_at
        FROM items WHERE parent_id IS NOT DISTINCT FROM $1 AND id != $2
        ORDER BY type DESC, name ASC
    """
    rows = await DatabasePool.fetch_all(siblings_q, parent_id, node_id)
    return [dict(row) for row in rows]

async def count_descendants(node_id: Union[UUID, str]) -> int:
    """
    Conta total de descendentes (sem incluir o próprio node).
    """
    q = """
        WITH RECURSIVE descendants AS (
            SELECT id FROM items WHERE id = $1
            UNION
            SELECT i.id FROM items i
            JOIN descendants d ON i.parent_id = d.id
        )
        SELECT COUNT(*) - 1 as count FROM descendants
    """
    result = await DatabasePool.fetch_one(q, node_id)
    return result["count"] if result else 0

async def get_directory_stats(node_id: Union[UUID, str]) -> Dict:
    """
    Retorna estatísticas de um diretório:
    total files, total folders, total size (se implementado).
    """
    q = """
        WITH RECURSIVE tree AS (
            SELECT id, type FROM items WHERE parent_id = $1
            UNION
            SELECT i.id, i.type FROM items i
            JOIN tree t ON i.parent_id = t.id
        )
        SELECT 
            COUNT(CASE WHEN type = 'FILE' THEN 1 END) as files,
            COUNT(CASE WHEN type = 'FOLDER' THEN 1 END) as folders,
            COUNT(*) as total
        FROM tree
    """
    result = await DatabasePool.fetch_one(q, node_id)
    return {
        "files": result["files"] or 0,
        "folders": result["folders"] or 0,
        "total": result["total"] or 0,
    }