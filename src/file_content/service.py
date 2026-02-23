from typing import Optional, Dict
from datetime import datetime
import hashlib

from src.db.connection import DatabasePool
from src.core.logging_config import get_logger

logger = get_logger(__name__)

def _compute_etag(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

async def _ensure_is_file(file_id: str) -> None:
    q = "SELECT id, type FROM items WHERE id = $1 LIMIT 1"
    row = await DatabasePool.fetch_one(q, file_id)
    if not row:
        raise FileNotFoundError("file_not_found")
    if row.get("type") != "FILE":
        raise TypeError("not_a_file")

async def get_file_content(file_id: str) -> Dict[str, Optional[str]]:
    """
    Retorna content e updated_at (se existir), garantido que o item existe e é FILE.
    If no content row exists, returns empty content with updated_at as None.
    """
    await _ensure_is_file(file_id)
    q = """
        SELECT content, updated_at
        FROM file_contents
        WHERE file_id = $1
        LIMIT 1
    """
    row = await DatabasePool.fetch_one(q, file_id)
    content = row["content"] if row else ""
    updated_at = row["updated_at"] if row else None
    etag = _compute_etag(content)
    return {"content": content, "updated_at": updated_at, "etag": etag}

async def save_file_content(file_id: str, content: str, user_id: Optional[str] = None) -> Dict[str, Optional[str]]:
    """
    Upsert content for file_id. Returns content, updated_at and etag.
    Attempts to set last_modified_by if column exists (non-fatal).
    """
    await _ensure_is_file(file_id)
    insert_q = """
        INSERT INTO file_contents (id, file_id, content, created_at, updated_at)
        VALUES (gen_random_uuid(), $1, $2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (file_id) DO UPDATE
          SET content = EXCLUDED.content,
              updated_at = CURRENT_TIMESTAMP
        RETURNING content, updated_at
    """
    row = await DatabasePool.fetch_one(insert_q, file_id, content)
    # try to update last_modified_by if column exists
    if user_id:
        try:
            await DatabasePool.execute(
                "UPDATE file_contents SET last_modified_by = $1 WHERE file_id = $2",
                user_id,
                file_id,
            )
        except Exception:
            # ignore if column does not exist
            logger.debug("last_modified_by column not present or update failed; continuing")
    content_ret = row["content"]
    updated_at = row["updated_at"]
    etag = _compute_etag(content_ret)
    return {"content": content_ret, "updated_at": updated_at, "etag": etag}