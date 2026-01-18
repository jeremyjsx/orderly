import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import SessionDep, require_admin
from app.core.schemas import PaginatedResponse
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
    try:
        category = await create_category(session, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return CategoryPublic(
        id=category.id,
        name=category.name,
        description=category.description,
        slug=category.slug,
        is_active=category.is_active,
    )


@router.get("/", response_model=PaginatedResponse[CategoryPublic])
async def list_categories_handler(
    session: SessionDep,
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=10, ge=1, le=100, description="Maximum number of records"
    ),
    active_only: bool = Query(default=False, description="Show only active categories"),
    search: str | None = Query(
        default=None, description="Search in category name, description, and slug"
    ),
) -> PaginatedResponse[CategoryPublic]:
    """List categories with pagination, filters, and search."""
    categories, total = await list_categories(
        session, offset=offset, limit=limit, active_only=active_only, search=search
    )

    items = [
        CategoryPublic(
            id=category.id,
            name=category.name,
            description=category.description,
            slug=category.slug,
            is_active=category.is_active,
        )
        for category in categories
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


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
    try:
        category = await update_category(session, category_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
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
