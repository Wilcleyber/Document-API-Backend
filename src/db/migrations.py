from src.db.connection import DatabasePool

MIGRATIONS = [
    # Migration 000: Garantir extensão para geração de UUID
    """
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
    """,

    # Migration 001: Criar tabelas base
    """
    CREATE TABLE IF NOT EXISTS items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        parent_id UUID REFERENCES items(id) ON DELETE CASCADE,
        type VARCHAR(10) NOT NULL CHECK (type IN ('FOLDER', 'FILE')),
        name VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    
    # Migration 002: Criar tabela de conteúdo separada
    """
    CREATE TABLE IF NOT EXISTS file_contents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        file_id UUID NOT NULL UNIQUE REFERENCES items(id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # Migration 003: Criar tabela de usuários
    """
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        username VARCHAR(64) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role VARCHAR(16) NOT NULL DEFAULT 'USER' CHECK (role IN ('ADMIN', 'USER')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    
    # Migration 004: Criar índices para otimização
    """
    CREATE INDEX IF NOT EXISTS idx_items_parent_id ON items(parent_id);
    CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
    CREATE INDEX IF NOT EXISTS idx_file_contents_file_id ON file_contents(file_id);
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    """,
]

class MigrationManager:
    """Gerencia migrações do banco de dados."""

    @staticmethod
    async def run_all_migrations() -> None:
        """Executa todas as migrações pendentes."""
        for i, migration in enumerate(MIGRATIONS, 1):
            try:
                await DatabasePool.execute(migration)
                print(f"✓ Migration {i:03d} executada com sucesso")
            except Exception as e:
                print(f"✗ Erro na Migration {i:03d}: {str(e)}")
                raise

    @staticmethod
    async def reset_database() -> None:
        """Limpa todo o banco (uso em desenvolvimento)."""
        queries = [
            "DROP TABLE IF EXISTS file_contents CASCADE;",
            "DROP TABLE IF EXISTS items CASCADE;",
        ]
        for query in queries:
            await DatabasePool.execute(query)
        print("✓ Banco de dados resetado")