from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import SessionDep, get_current_user
from app.core.security import create_access_token, verify_password
from app.modules.auth.schemas import Token
from app.modules.users.models import User
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


@router.post("/login", response_model=Token)
async def login(payload: UserCreate, session: SessionDep) -> Token:
    user = await get_user_by_email(session, payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token(user.id)

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic(id=current_user.id, email=current_user.email)
