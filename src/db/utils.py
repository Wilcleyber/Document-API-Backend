from typing import Optional, List, Union
from uuid import UUID
from src.db.connection import DatabasePool
from src.db.transactions import TransactionManager

class DatabaseUtils:
    """Utilitários para operações comuns no banco de dados."""

    @staticmethod
    async def fetch_by_id(item_id: Union[UUID, str]) -> Optional[dict]:
        """Busca um item por ID."""
        query = """
            SELECT id, parent_id, type, name, created_at, updated_at
            FROM items WHERE id = $1
        """
        return await DatabasePool.fetch_one(query, item_id)

    @staticmethod
    async def list_children(parent_id: Union[UUID, str]) -> List[dict]:
        """Lista todos os filhos diretos de um parent."""
        query = """
            SELECT id, parent_id, type, name, created_at, updated_at
            FROM items WHERE parent_id = $1
            ORDER BY name ASC
        """
        return await DatabasePool.fetch_all(query, parent_id)

    @staticmethod
    async def delete_cascade(item_id: Union[UUID, str]) -> None:
        """
        Exclusão em cascata lógica (com transação).
        Opção: ON DELETE CASCADE no FK (automático no DB).
        """
        async with TransactionManager.transaction() as conn:
            # Busca todos os descendentes recursivamente
            query = """
                WITH RECURSIVE descendants AS (
                    SELECT id FROM items WHERE id = $1
                    UNION
                    SELECT i.id FROM items i
                    JOIN descendants d ON i.parent_id = d.id
                )
                DELETE FROM items WHERE id IN (SELECT id FROM descendants)
            """
            await conn.execute(query, item_id)

    @staticmethod
    async def get_file_content(file_id: Union[UUID, str]) -> Optional[str]:
        """Retorna o conteúdo de um arquivo."""
        query = """
            SELECT content FROM file_contents WHERE file_id = $1
        """
        result = await DatabasePool.fetch_one(query, file_id)
        return result['content'] if result else None

    @staticmethod
    async def save_file_content(file_id: Union[UUID, str], content: str) -> None:
        """Salva ou atualiza conteúdo de arquivo."""
        query = """
            INSERT INTO file_contents (file_id, content)
            VALUES ($1, $2)
            ON CONFLICT (file_id) DO UPDATE SET content = $2, updated_at = CURRENT_TIMESTAMP
        """
        await DatabasePool.execute(query, file_id, content)

    @staticmethod
    async def get_tree(parent_id: Optional[Union[UUID, str]] = None) -> List[dict]:
        """Retorna a árvore de itens (com recursão otimizada)."""
        query = """
            WITH RECURSIVE tree AS (
                SELECT id, parent_id, type, name, created_at, updated_at, 1 as level
                FROM items WHERE parent_id IS NULL OR parent_id = $1
                UNION
                SELECT i.id, i.parent_id, i.type, i.name, i.created_at, i.updated_at, t.level + 1
                FROM items i
                JOIN tree t ON i.parent_id = t.id
            )
            SELECT * FROM tree ORDER BY level, name
        """
        return await DatabasePool.fetch_all(query, parent_id)