from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FileContentOut(BaseModel):
    content: str
    updated_at: Optional[datetime]
    etag: str

class FileContentUpdate(BaseModel):
    content: str