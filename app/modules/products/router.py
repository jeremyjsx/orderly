import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import SessionDep, require_admin
from app.core.schemas import PaginatedResponse
from app.modules.products.repo import (
    create_product,
    get_product_by_id,
    list_products,
    update_product,
)
from app.modules.products.schemas import ProductCreate, ProductPublic, ProductUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductPublic, status_code=status.HTTP_201_CREATED)
async def create_product_handler(
    payload: ProductCreate,
    session: SessionDep,
    admin_user: User = Depends(require_admin),
) -> ProductPublic:
    product = await create_product(session, payload)
    return ProductPublic(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category_id=product.category_id,
        image_url=product.image_url,
        is_active=product.is_active,
    )


@router.get("/{product_id}", response_model=ProductPublic)
async def get_product_handler(
    product_id: uuid.UUID, session: SessionDep
) -> ProductPublic:
    product = await get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return ProductPublic(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category_id=product.category_id,
        image_url=product.image_url,
        is_active=product.is_active,
    )


@router.get("/", response_model=PaginatedResponse[ProductPublic])
async def list_products_handler(
    session: SessionDep,
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=10, ge=1, le=100, description="Maximum number of records"
    ),
    category_id: uuid.UUID | None = Query(
        default=None, description="Filter by category ID"
    ),
    active_only: bool = Query(default=False, description="Show only active products"),
) -> PaginatedResponse[ProductPublic]:
    """List products with pagination and optional filters."""
    products, total = await list_products(
        session,
        offset=offset,
        limit=limit,
        category_id=category_id,
        active_only=active_only,
    )

    items = [
        ProductPublic(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            stock=product.stock,
            category_id=product.category_id,
            image_url=product.image_url,
            is_active=product.is_active,
        )
        for product in products
    ]

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

    return ProductPublic(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category_id=product.category_id,
        image_url=product.image_url,
        is_active=product.is_active,
    )
