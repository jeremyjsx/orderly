import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionDep
from app.modules.categories.models import Category
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate


async def create_category(
    session: SessionDep, category_data: CategoryCreate
) -> Category:
    try:
        category = Category(
            id=uuid.uuid4(),
            name=category_data.name,
            description=category_data.description,
            slug=category_data.slug,
            is_active=category_data.is_active,
        )
        session.add(category)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    await session.refresh(category)
    return category


async def get_category_by_id(
    session: SessionDep, category_id: uuid.UUID
) -> Category | None:
    result = await session.execute(select(Category).where(Category.id == category_id))
    return result.scalar_one_or_none()


async def get_category_by_slug(session: SessionDep, slug: str) -> Category | None:
    result = await session.execute(select(Category).where(Category.slug == slug))
    return result.scalar_one_or_none()


async def list_categories(
    session: SessionDep, offset: int = 0, limit: int = 10, active_only: bool = False
) -> Sequence[Category]:
    query = select(Category)
    if active_only:
        query = query.where(Category.is_active)
    result = await session.execute(query.offset(offset).limit(limit))
    return result.scalars().all()


async def update_category(
    session: SessionDep, category_id: uuid.UUID, category_data: CategoryUpdate
) -> Category | None:
    category = await get_category_by_id(session, category_id)
    if not category:
        return None

    try:
        if category_data.name is not None:
            category.name = category_data.name
        if category_data.description is not None:
            category.description = category_data.description
        if category_data.slug is not None:
            category.slug = category_data.slug
        if category_data.is_active is not None:
            category.is_active = category_data.is_active

        await session.commit()
        await session.refresh(category)
    except IntegrityError:
        await session.rollback()
        raise
    return category


async def delete_category(session: SessionDep, category_id: uuid.UUID) -> bool:
    category = await get_category_by_id(session, category_id)
    if not category:
        return False

    try:
        await session.delete(category)
        await session.commit()
        return True
    except IntegrityError:
        await session.rollback()
        raise
