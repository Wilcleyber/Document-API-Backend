from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from uuid import UUID
from src.file_content.schemas import FileContentOut, FileContentUpdate
from src.file_content import service
from src.auth.dependencies import get_current_user
from src.authorization.dependencies import require_edit_permission
from src.auth.schemas import TokenPayload
from src.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/files", tags=["files"])

@router.get("/{file_id}/content", response_model=FileContentOut)
async def get_content(
    file_id: Union[UUID, str],
    response: Response,
    current_user: TokenPayload = Depends(get_current_user),
):
    try:
        data = await service.get_file_content(file_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="file_not_found")
    except TypeError:
        raise HTTPException(status_code=400, detail="not_a_file")
    except Exception as e:
        logger.error("Error fetching file content", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")
    # set ETag header
    response.headers["ETag"] = data["etag"]
    return FileContentOut(content=data["content"], updated_at=data["updated_at"], etag=data["etag"])

@router.put("/{file_id}/content", response_model=FileContentOut)
async def put_content(
    file_id: Union[UUID, str],
    payload: FileContentUpdate,
    request: Request,
    current_user: TokenPayload = Depends(require_edit_permission("file_id")),
):
    """
    Update content. Requires If-Match header with ETag to avoid lost updates (optional).
    Both USER and ADMIN allowed (require_edit_permission enforces).
    """
    # optimistic concurrency via If-Match header (optional)
    if_match = request.headers.get("if-match")
    try:
        if if_match:
            existing = await service.get_file_content(file_id)
            if existing["etag"] != if_match:
                raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED, detail="etag_mismatch")
        result = await service.save_file_content(file_id, payload.content, user_id=getattr(current_user, "user_id", None))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="file_not_found")
    except TypeError:
        raise HTTPException(status_code=400, detail="not_a_file")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error saving file content", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")
    # set ETag header on response
    resp = FileContentOut(content=result["content"], updated_at=result["updated_at"], etag=result["etag"])
    return resp