import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionDep
from app.modules.products.models import Product
from app.modules.products.schemas import ProductCreate


async def create_product(session: SessionDep, product_data: ProductCreate) -> Product:
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
    session: SessionDep, offset: int = 0, limit: int = 10
) -> Sequence[Product]:
    result = await session.execute(select(Product).offset(offset).limit(limit))
    return result.scalars().all()
