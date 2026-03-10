from fastapi import APIRouter, HTTPException, status
from src.users.schemas import UserCreate, UserOut, DemoCredentials
from src.users import service
from src.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate):
    try:
        user = await service.create_user(payload)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creating user", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")

@router.get("/demo", response_model=DemoCredentials)
async def demo_credentials():
    try:
        creds = await service.get_or_create_demo_user()
        return creds
    except PermissionError:
        raise HTTPException(status_code=403, detail="demo_disabled_in_production")
    except Exception as e:
        logger.error("Error retrieving demo credentials", exc_info=True)
        raise HTTPException(status_code=500, detail="internal_server_error")


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: Union[UUID, str]):
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    return user