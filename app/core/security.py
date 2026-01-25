import uuid
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_EXPIRATION_TIME)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str]:
    """
    Create a refresh token with a unique ID (jti).

    Returns:
        Tuple of (token, jti) - jti is needed to store/validate in Redis
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh", "jti": jti}
    token = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return token, jti


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        sub = payload.get("sub")
        token_type = payload.get("type", "access")
        if not sub:
            raise ValueError("Missing sub in token")
        if token_type != "access":
            raise ValueError("Invalid token type")
        return uuid.UUID(sub)
    except (JWTError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from err


def decode_refresh_token(token: str) -> tuple[uuid.UUID, str]:
    """
    Decode refresh token and extract user_id and jti.

    Returns:
        Tuple of (user_id, jti)
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        sub = payload.get("sub")
        token_type = payload.get("type")
        jti = payload.get("jti")
        if not sub:
            raise ValueError("Missing sub in token")
        if token_type != "refresh":
            raise ValueError("Invalid token type")
        if not jti:
            raise ValueError("Missing jti in token")
        return uuid.UUID(sub), jti
    except (JWTError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from err
