from typing import Optional
from src.auth.schemas import TokenPayload
from src.db.connection import DatabasePool

async def can_manage_node(user: TokenPayload) -> bool:
    """ADMIN only."""
    return getattr(user, "role", None) == "ADMIN"

async def can_edit_content(user: TokenPayload, file_id: str) -> bool:
    """
    USERs may edit files they are allowed to (simple global policy).
    ADMIN can always edit.
    Returns True/False (does not raise HTTP errors).
    """
    if getattr(user, "role", None) == "ADMIN":
        return True

    # Ensure target exists and is a FILE
    q = "SELECT type FROM items WHERE id = $1 LIMIT 1"
    row = await DatabasePool.fetch_one(q, file_id)
    if not row:
        return False
    return row.get("type") == "FILE"