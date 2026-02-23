from typing import Callable, Iterable
from fastapi import Depends, HTTPException, Request, status
from src.auth.dependencies import get_current_user
from src.auth.schemas import TokenPayload
from src.authorization.rules import can_edit_content, can_manage_node

def require_roles(*allowed_roles: str) -> Callable:
    """
    Dependency factory: require one of allowed_roles.
    Usage: Depends(require_roles("ADMIN")) or Depends(require_roles("ADMIN", "USER"))
    """
    async def dependency(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient_role")
        return current_user
    return dependency

def require_admin() -> Callable:
    """Shorthand for requiring ADMIN role."""
    return require_roles("ADMIN")

def require_edit_permission(path_param: str = "file_id") -> Callable:
    """
    Dependency factory that checks whether current_user can edit the file identified
    by the path parameter named `path_param`.
    Usage: Depends(require_edit_permission("file_id")) where route has path param {file_id}.
    """
    async def dependency(request: Request, current_user: TokenPayload = Depends(get_current_user)):
        file_id = request.path_params.get(path_param)
        if not file_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_file_id")
        allowed = await can_edit_content(current_user, file_id)
        if not allowed:
            # Distinguish not found vs forbidden
            from src.db.connection import DatabasePool
            row = await DatabasePool.fetch_one("SELECT id FROM items WHERE id = $1", file_id)
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file_not_found")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient_permissions")
        return current_user
    return dependency

def require_manage_node() -> Callable:
    """
    Dependency that allows only ADMINs to manage nodes (create/delete/rename).
    Usage: Depends(require_manage_node())
    """
    async def dependency(current_user: TokenPayload = Depends(get_current_user)):
        if not await can_manage_node(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_access_required")
        return current_user
    return dependency