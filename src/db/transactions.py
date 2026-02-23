from contextlib import asynccontextmanager
from src.db.connection import DatabasePool

class TransactionManager:
    """Gerencia transações seguras (begin/commit/rollback)."""

    @staticmethod
    @asynccontextmanager
    async def transaction():
        """Context manager para transações."""
        conn = await DatabasePool.get_connection()
        try:
            async with conn.transaction():
                yield conn
        finally:
            await DatabasePool._pool.release(conn)

    @staticmethod
    async def begin(conn) -> None:
        """Inicia transação."""
        await conn.execute("BEGIN")

    @staticmethod
    async def commit(conn) -> None:
        """Commit da transação."""
        await conn.execute("COMMIT")

    @staticmethod
    async def rollback(conn) -> None:
        """Rollback da transação."""
        await conn.execute("ROLLBACK")