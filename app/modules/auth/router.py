from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import SessionDep
from app.modules.users.repo import create_user, get_user_by_email
from app.modules.users.schemas import UserCreate, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def register(payload: UserCreate, session: SessionDep) -> UserPublic:
    existing = await get_user_by_email(session, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    try:
        created = await create_user(session, payload.email, payload.password)
    except IntegrityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        ) from err

    return UserPublic(id=created.id, email=created.email)
