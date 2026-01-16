import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SessionDep, require_admin
from app.modules.products.repo import create_product, get_product_by_id, list_products
from app.modules.products.schemas import ProductCreate, ProductPublic
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


@router.get("/", response_model=list[ProductPublic])
async def list_products_handler(session: SessionDep) -> list[ProductPublic]:
    products = await list_products(session)
    return [
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
