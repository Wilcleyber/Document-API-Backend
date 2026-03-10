import asyncpg
from typing import Optional, List, Union
from src.core.config import Settings

class DatabasePool:
    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def initialize(cls, settings: Settings) -> None:
        """Inicializa o pool de conexões com PostgreSQL (Neon)."""
        cls._pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=5,
            max_size=20,
            command_timeout=60,
        )

    @classmethod
    async def close(cls) -> None:
        """Fecha o pool de conexões."""
        if cls._pool:
            await cls._pool.close()

    @classmethod
    async def get_connection(cls) -> asyncpg.Connection:
        """Retorna uma conexão do pool."""
        if not cls._pool:
            raise RuntimeError("DatabasePool não foi inicializado")
        return await cls._pool.acquire()

    @classmethod
    async def execute(cls, query: str, *args) -> None:
        """Executa query sem retorno."""
        conn = await cls.get_connection()
        try:
            await conn.execute(query, *args)
        finally:
            await cls._pool.release(conn)

    @classmethod
    async def fetch_one(cls, query: str, *args) -> Optional[dict]:
        """Retorna um registro."""
        conn = await cls.get_connection()
        try:
            result = await conn.fetchrow(query, *args)
            return dict(result) if result else None
        finally:
            await cls._pool.release(conn)

    @classmethod
    async def fetch_all(cls, query: str, *args) -> list[dict]:
        """Retorna múltiplos registros."""
        conn = await cls.get_connection()
        try:
            results = await conn.fetch(query, *args)
            return [dict(r) for r in results]
        finally:
            await cls._pool.release(conn)