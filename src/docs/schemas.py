from pydantic import BaseModel
from typing import Optional, List, Union

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None