import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import SessionDep, get_current_user, require_admin
from app.core.schemas import PaginatedResponse
from app.modules.users.models import User
from app.modules.users.repo import (
    delete_user,
    get_user_by_id,
    list_users,
    update_user,
    update_user_password,
)
from app.modules.users.schemas import PasswordChange, UserPublic, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _get_role_value(user: User) -> str:
    """Get role value as string from user."""
    if hasattr(user.role, "value"):
        return user.role.value
    return str(user.role)


@router.get("/me", response_model=UserPublic)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserPublic:
    """Get current authenticated user's profile."""
    return UserPublic(
        id=current_user.id,
        email=current_user.email,
        role=_get_role_value(current_user),
    )


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    payload: PasswordChange,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> None:
    """Change current authenticated user's password."""
    try:
        await update_user_password(
            session,
            current_user.id,
            payload.current_password,
            payload.new_password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/", response_model=PaginatedResponse[UserPublic])
async def list_users_handler(
    session: SessionDep,
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=10, ge=1, le=100, description="Maximum number of records"
    ),
    admin_user: User = Depends(require_admin),
) -> PaginatedResponse[UserPublic]:
    """List all users with pagination (admin only)."""
    users, total = await list_users(session, offset=offset, limit=limit)

    items = [
        UserPublic(id=user.id, email=user.email, role=_get_role_value(user))
        for user in users
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/{user_id}", response_model=UserPublic)
async def get_user_handler(
    user_id: uuid.UUID,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> UserPublic:
    """Get user by ID (admin only)."""
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserPublic(
        id=user.id, email=user.email, role=_get_role_value(user)
    )


@router.patch("/{user_id}", response_model=UserPublic)
async def update_user_handler(
    user_id: uuid.UUID,
    payload: UserUpdate,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> UserPublic:
    """Update user by ID (admin only)."""
    if payload.email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided",
        )

    try:
        updated_user = await update_user(session, user_id, email=payload.email)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserPublic(
        id=updated_user.id,
        email=updated_user.email,
        role=_get_role_value(updated_user),
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_handler(
    user_id: uuid.UUID,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> None:
    """Delete a user by ID (hard delete, admin only)."""
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    deleted = await delete_user(session, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
