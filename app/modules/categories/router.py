import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SessionDep, require_admin
from app.modules.categories.repo import (
    create_category,
    delete_category,
    get_category_by_id,
    get_category_by_slug,
    list_categories,
    update_category,
)
from app.modules.categories.schemas import (
    CategoryCreate,
    CategoryPublic,
    CategoryUpdate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
async def create_category_handler(
    payload: CategoryCreate,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> CategoryPublic:
    category = await create_category(session, payload)
    return CategoryPublic(
        id=category.id,
        name=category.name,
        description=category.description,
        slug=category.slug,
        is_active=category.is_active,
    )


@router.get("/", response_model=list[CategoryPublic])
async def list_categories_handler(
    session: SessionDep, offset: int = 0, limit: int = 10, active_only: bool = False
) -> list[CategoryPublic]:
    categories = await list_categories(session, offset, limit, active_only)
    return [
        CategoryPublic(
            id=category.id,
            name=category.name,
            description=category.description,
            slug=category.slug,
            is_active=category.is_active,
        )
        for category in categories
    ]


@router.get("/{category_id}", response_model=CategoryPublic)
async def get_category_handler(
    category_id: uuid.UUID, session: SessionDep
) -> CategoryPublic:
    category = await get_category_by_id(session, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return CategoryPublic(
        id=category.id,
        name=category.name,
        description=category.description,
        slug=category.slug,
        is_active=category.is_active,
    )


@router.get("/slug/{slug}", response_model=CategoryPublic)
async def get_category_by_slug_handler(
    slug: str, session: SessionDep
) -> CategoryPublic:
    category = await get_category_by_slug(session, slug)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return CategoryPublic(
        id=category.id,
        name=category.name,
        description=category.description,
        slug=category.slug,
        is_active=category.is_active,
    )


@router.patch("/{category_id}", response_model=CategoryPublic)
async def update_category_handler(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> CategoryPublic:
    category = await update_category(session, category_id, payload)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return CategoryPublic(
        id=category.id,
        name=category.name,
        description=category.description,
        slug=category.slug,
        is_active=category.is_active,
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category_handler(
    category_id: uuid.UUID,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> None:
    deleted = await delete_category(session, category_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
