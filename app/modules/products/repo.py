import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionDep
from app.modules.cart.repo import delete_cart_items_by_product_id
from app.modules.categories.repo import get_category_by_id
from app.modules.products.models import Product
from app.modules.products.schemas import ProductCreate, ProductUpdate


async def create_product(session: SessionDep, product_data: ProductCreate) -> Product:
    category = await get_category_by_id(session, product_data.category_id)
    if not category:
        raise ValueError(f"Category with id {product_data.category_id} not found")

    if not category.is_active:
        raise ValueError(
            f"Cannot create product in inactive category "
            f"with id {product_data.category_id}"
        )

    try:
        product = Product(
            id=uuid.uuid4(),
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            stock=product_data.stock,
            category_id=product_data.category_id,
            image_url=product_data.image_url,
            is_active=True,
        )
        session.add(product)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    await session.refresh(product)
    return product


async def get_product_by_id(
    session: SessionDep, product_id: uuid.UUID
) -> Product | None:
    result = await session.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def list_products(
    session: SessionDep,
    offset: int = 0,
    limit: int = 10,
    category_id: uuid.UUID | None = None,
    active_only: bool = False,
    search: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort_by: str | None = None,
) -> tuple[Sequence[Product], int]:
    """List products with pagination, filters, search, and sorting."""
    query = select(Product)

    if category_id is not None:
        query = query.where(Product.category_id == category_id)
    if active_only:
        query = query.where(Product.is_active)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern),
            )
        )
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    if sort_by:
        if sort_by == "price":
            query = query.order_by(Product.price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Product.price.desc())
        elif sort_by == "name":
            query = query.order_by(Product.name.asc())
        elif sort_by == "name_desc":
            query = query.order_by(Product.name.desc())
        elif sort_by == "created_at":
            query = query.order_by(Product.created_at.asc())
        elif sort_by == "created_at_desc":
            query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    products = result.scalars().all()

    return products, total


async def update_product(
    session: SessionDep, product_id: uuid.UUID, product_data: ProductUpdate
) -> Product | None:
    product = await get_product_by_id(session, product_id)
    if not product:
        return None

    if product_data.category_id is not None:
        category = await get_category_by_id(session, product_data.category_id)
        if not category:
            raise ValueError(f"Category with id {product_data.category_id} not found")
        if not category.is_active:
            raise ValueError(
                f"Cannot update product to inactive category "
                f"with id {product_data.category_id}"
            )

    try:
        if product_data.name is not None:
            product.name = product_data.name
        if product_data.description is not None:
            product.description = product_data.description
        if product_data.price is not None:
            product.price = product_data.price
        if product_data.stock is not None:
            product.stock = product_data.stock
        if product_data.category_id is not None:
            product.category_id = product_data.category_id
        if product_data.image_url is not None:
            product.image_url = product_data.image_url
        if product_data.is_active is not None:
            product.is_active = product_data.is_active

        await session.commit()
        await session.refresh(product)
    except IntegrityError:
        await session.rollback()
        raise
    return product


async def delete_product(session: SessionDep, product_id: uuid.UUID) -> bool:
    """Delete a product by ID (hard delete).

    Also removes the product from all active shopping carts.
    """
    product = await get_product_by_id(session, product_id)
    if not product:
        return False

    await delete_cart_items_by_product_id(session, product_id)

    try:
        await session.delete(product)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    return True
