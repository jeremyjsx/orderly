from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import SessionDep, get_current_user
from app.core.config import settings
from app.core.rate_limit import RateLimitStrategy, create_rate_limiter
from app.core.redis import (
    revoke_all_user_tokens,
    revoke_refresh_token,
    store_refresh_token,
    validate_refresh_token,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)
from app.modules.auth.schemas import RefreshTokenRequest, Token
from app.modules.users.models import User
from app.modules.users.repo import create_user, get_user_by_email, get_user_by_id
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
    refresh_token, jti = create_refresh_token(user.id)

    await store_refresh_token(str(user.id), jti, settings.JWT_REFRESH_EXPIRATION_DAYS)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    request: Request,
    session: SessionDep,
    _: None = Depends(rate_limit_auth),
) -> Token:
    """Get new access and refresh tokens using a valid refresh token."""
    user_id, jti = decode_refresh_token(payload.refresh_token)

    is_valid = await validate_refresh_token(str(user_id), jti)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked or is invalid",
        )

    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    await revoke_refresh_token(str(user_id), jti)

    access_token = create_access_token(user.id)
    new_refresh_token, new_jti = create_refresh_token(user.id)

    await store_refresh_token(
        str(user.id), new_jti, settings.JWT_REFRESH_EXPIRATION_DAYS
    )

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshTokenRequest,
    request: Request,
    _: None = Depends(rate_limit_auth),
) -> None:
    """Logout by revoking the refresh token."""
    try:
        user_id, jti = decode_refresh_token(payload.refresh_token)
        await revoke_refresh_token(str(user_id), jti)
    except HTTPException:
        pass


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    current_user: User = Depends(get_current_user),
) -> None:
    """Logout from all devices by revoking all refresh tokens for the user."""
    await revoke_all_user_tokens(str(current_user.id))
