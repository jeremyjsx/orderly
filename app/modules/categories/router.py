import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.api.deps import SessionDep, require_admin
from app.core.s3 import delete_category_image, upload_category_image
from app.core.schemas import PaginatedResponse
from app.modules.categories.repo import (
    create_category,
    delete_category,
    get_category_by_id,
    get_category_by_slug,
    list_categories,
    update_category,
    update_category_image,
)
from app.modules.categories.schemas import (
    CategoryCreate,
    CategoryPublic,
    CategoryUpdate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/categories", tags=["categories"])


def _to_public(category) -> CategoryPublic:
    return CategoryPublic(
        id=category.id,
        name=category.name,
        description=category.description,
        slug=category.slug,
        is_active=category.is_active,
        image_url=category.image_url,
    )


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
    return _to_public(category)


@router.get("/", response_model=PaginatedResponse[CategoryPublic])
async def list_categories_handler(
    session: SessionDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    active_only: bool = Query(default=False),
    search: str | None = Query(default=None),
) -> PaginatedResponse[CategoryPublic]:
    categories, total = await list_categories(
        session, offset=offset, limit=limit, active_only=active_only, search=search
    )
    items = [_to_public(category) for category in categories]
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
    return _to_public(category)


@router.get("/slug/{slug}", response_model=CategoryPublic)
async def get_category_by_slug_handler(
    slug: str, session: SessionDep
) -> CategoryPublic:
    category = await get_category_by_slug(session, slug)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return _to_public(category)


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
    return _to_public(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category_handler(
    category_id: uuid.UUID,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> None:
    category = await get_category_by_id(session, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    image_url = category.image_url
    deleted = await delete_category(session, category_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    if image_url:
        await delete_category_image(image_url)


@router.put("/{category_id}/image", response_model=CategoryPublic)
async def upload_category_image_handler(
    category_id: uuid.UUID,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
    image: UploadFile = File(...),
) -> CategoryPublic:
    category = await get_category_by_id(session, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    old_image_url = category.image_url
    new_image_url = await upload_category_image(image)

    category = await update_category_image(session, category_id, new_image_url)

    if old_image_url:
        await delete_category_image(old_image_url)

    return _to_public(category)


@router.delete("/{category_id}/image", response_model=CategoryPublic)
async def delete_category_image_handler(
    category_id: uuid.UUID,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> CategoryPublic:
    category = await get_category_by_id(session, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    if not category.image_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category has no image"
        )

    old_image_url = category.image_url
    category = await update_category_image(session, category_id, None)
    await delete_category_image(old_image_url)

    return _to_public(category)
