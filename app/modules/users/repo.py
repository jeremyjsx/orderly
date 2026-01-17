import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password
from app.db.session import SessionDep
from app.modules.cart.repo import delete_cart_by_user_id
from app.modules.users.models import User


async def create_user(session: SessionDep, email: str, password: str) -> User:
    user = User(id=uuid.uuid4(), email=email, hashed_password=hash_password(password))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    await session.refresh(user)
    return user


async def get_user_by_email(session: SessionDep, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: SessionDep, user_id: uuid.UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def list_users(
    session: SessionDep,
    offset: int = 0,
    limit: int = 10,
) -> tuple[Sequence[User], int]:
    """List users with pagination."""
    query = select(User)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    users = result.scalars().all()

    return users, total


async def update_user(
    session: SessionDep, user_id: uuid.UUID, email: str | None = None
) -> User | None:
    user = await get_user_by_id(session, user_id)
    if not user:
        return None

    if email is not None:
        existing = await get_user_by_email(session, email)
        if existing and existing.id != user_id:
            raise ValueError(f"Email {email} is already taken")
        user.email = email

    try:
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()
        raise
    return user


async def update_user_password(
    session: SessionDep, user_id: uuid.UUID, current_password: str, new_password: str
) -> User | None:
    user = await get_user_by_id(session, user_id)
    if not user:
        return None

    if not verify_password(current_password, user.hashed_password):
        raise ValueError("Current password is incorrect")

    user.hashed_password = hash_password(new_password)

    try:
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()
        raise
    return user


async def delete_user(session: SessionDep, user_id: uuid.UUID) -> bool:
    """Delete a user by ID (hard delete).

    Cart deletion is handled automatically via FK CASCADE.
    Orders are preserved with their original user_id (no FK constraint).
    """
    user = await get_user_by_id(session, user_id)
    if not user:
        return False

    await delete_cart_by_user_id(session, user_id)

    try:
        await session.delete(user)
        await session.commit()
        return True
    except IntegrityError:
        await session.rollback()
        raise
