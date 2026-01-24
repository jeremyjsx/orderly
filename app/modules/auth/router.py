from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import SessionDep
from app.core.config import settings
from app.core.rate_limit import RateLimitStrategy, create_rate_limiter
from app.core.security import create_access_token, verify_password
from app.modules.auth.schemas import Token
from app.modules.users.repo import create_user, get_user_by_email
from app.modules.users.schemas import UserCreate, UserPublic
from app.modules.users.utils import get_role_value

router = APIRouter(prefix="/auth", tags=["auth"])

auth_rate_limiter = create_rate_limiter(
    requests=settings.RATE_LIMIT_AUTH_REQUESTS,
    window_seconds=settings.RATE_LIMIT_AUTH_WINDOW,
    strategy=RateLimitStrategy.IP,
)


async def rate_limit_auth(request: Request) -> None:
    """Dependency for rate limiting auth endpoints."""
    if settings.RATE_LIMIT_ENABLED:
        endpoint = f"{request.method}:{request.url.path}"
        await auth_rate_limiter(request, endpoint, user=None)


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: UserCreate,
    request: Request,
    session: SessionDep,
    _: None = Depends(rate_limit_auth),
) -> UserPublic:
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

    return UserPublic(id=created.id, email=created.email, role=get_role_value(created))


@router.post("/login", response_model=Token)
async def login(
    payload: UserCreate,
    request: Request,
    session: SessionDep,
    _: None = Depends(rate_limit_auth),
) -> Token:
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
