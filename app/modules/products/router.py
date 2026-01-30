import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.api.deps import SessionDep, require_admin
from app.core.s3 import delete_product_image, upload_product_image
from app.core.schemas import PaginatedResponse
from app.modules.products.repo import (
    create_product,
    delete_product,
    get_product_by_id,
    list_products,
    update_product,
    update_product_image,
)
from app.modules.products.schemas import ProductCreate, ProductPublic, ProductUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/products", tags=["products"])


def _to_public(product) -> ProductPublic:
    return ProductPublic(
        id=product.id,
        name=product.name,
        description=product.description,
        price=float(product.price),
        stock=product.stock,
        category_id=product.category_id,
        image_url=product.image_url,
        is_active=product.is_active,
    )


@router.post("/", response_model=ProductPublic, status_code=status.HTTP_201_CREATED)
async def create_product_handler(
    payload: ProductCreate,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> ProductPublic:
    try:
        product = await create_product(session, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return _to_public(product)


@router.get("/{product_id}", response_model=ProductPublic)
async def get_product_handler(
    product_id: uuid.UUID, session: SessionDep
) -> ProductPublic:
    product = await get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return _to_public(product)


@router.get("/", response_model=PaginatedResponse[ProductPublic])
async def list_products_handler(
    session: SessionDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    category_id: uuid.UUID | None = Query(default=None),
    active_only: bool = Query(default=False),
    search: str | None = Query(default=None),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    sort_by: str | None = Query(default=None),
) -> PaginatedResponse[ProductPublic]:
    products, total = await list_products(
        session,
        offset=offset,
        limit=limit,
        category_id=category_id,
        active_only=active_only,
        search=search,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
    )
    items = [_to_public(product) for product in products]
    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.patch("/{product_id}", response_model=ProductPublic)
async def update_product_handler(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> ProductPublic:
    try:
        product = await update_product(session, product_id, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return _to_public(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_handler(
    product_id: uuid.UUID,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> None:
    product = await get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    image_url = product.image_url

    try:
        deleted = await delete_product(session, product_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    if image_url:
        await delete_product_image(image_url)


@router.put("/{product_id}/image", response_model=ProductPublic)
async def upload_product_image_handler(
    product_id: uuid.UUID,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
    image: UploadFile = File(...),
) -> ProductPublic:
    product = await get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    old_image_url = product.image_url
    new_image_url = await upload_product_image(image)

    product = await update_product_image(session, product_id, new_image_url)

    if old_image_url:
        await delete_product_image(old_image_url)

    return _to_public(product)


@router.delete("/{product_id}/image", response_model=ProductPublic)
async def delete_product_image_handler(
    product_id: uuid.UUID,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> ProductPublic:
    product = await get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    if not product.image_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product has no image"
        )

    old_image_url = product.image_url
    product = await update_product_image(session, product_id, None)
    await delete_product_image(old_image_url)

    return _to_public(product)
