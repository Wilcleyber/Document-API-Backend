from passlib.context import CryptContext
from typing import Optional, List, Union
from uuid import UUID
from src.db.connection import DatabasePool
from src.users.schemas import UserCreate, UserOut, DemoCredentials
from src.core.config import settings
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_ROLE = "USER"
DEMO_USERNAME = "demo"
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo-password"  # override via env if needed (non-prod)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_user(payload: UserCreate) -> UserOut:
    # prevent admin assignment via client
    role = DEFAULT_ROLE
    # check uniqueness
    exists_q = "SELECT id FROM users WHERE username = $1 OR email = $2 LIMIT 1"
    found = await DatabasePool.fetch_one(exists_q, payload.username, payload.email)
    if found:
        raise ValueError("username_or_email_already_exists")
    pwd_hash = hash_password(payload.password)
    insert_q = """
        INSERT INTO users (id, username, email, password_hash, role)
        VALUES (gen_random_uuid(), $1, $2, $3, $4)
        RETURNING id, username, email, role, created_at
    """
    row = await DatabasePool.fetch_one(insert_q, payload.username, payload.email, pwd_hash, role)
    return UserOut(**row)

async def get_user_by_id(user_id: Union[UUID, str]) -> Optional[UserOut]:
    q = "SELECT id, username, email, role, created_at FROM users WHERE id = $1"
    row = await DatabasePool.fetch_one(q, user_id)
    return UserOut(**row) if row else None

async def get_or_create_demo_user() -> DemoCredentials:
    # only allow demo creation in non-production
    if settings.is_production:
        raise PermissionError("Demo endpoint disabled in production")
    q = "SELECT username, email FROM users WHERE username = $1 LIMIT 1"
    found = await DatabasePool.fetch_one(q, DEMO_USERNAME)
    if found:
        return DemoCredentials(username=found["username"], email=found["email"], password=DEMO_PASSWORD)
    # create demo user
    payload = UserCreate(username=DEMO_USERNAME, email=DEMO_EMAIL, password=DEMO_PASSWORD)
    try:
        user = await create_user(payload)
        logger.info("Demo user created", extra={"username": user.username})
    except Exception:
        # possible race / already exists
        pass
    return DemoCredentials(username=DEMO_USERNAME, email=DEMO_EMAIL, password=DEMO_PASSWORD)