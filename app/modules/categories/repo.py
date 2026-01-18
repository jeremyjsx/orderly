import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionDep
from app.modules.categories.models import Category
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate


async def create_category(
    session: SessionDep, category_data: CategoryCreate
) -> Category:
    existing = await get_category_by_slug(session, category_data.slug)
    if existing:
        raise ValueError(f"Category with slug '{category_data.slug}' already exists")

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
    except IntegrityError as err:
        await session.rollback()
        raise ValueError(f"Category with slug '{category_data.slug}' already exists") from err
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
    session: SessionDep,
    offset: int = 0,
    limit: int = 10,
    active_only: bool = False,
    search: str | None = None,
) -> tuple[Sequence[Category], int]:
    """List categories with pagination, filters, and search."""
    query = select(Category)

    if active_only:
        query = query.where(Category.is_active)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Category.name.ilike(search_pattern),
                Category.description.ilike(search_pattern),
                Category.slug.ilike(search_pattern),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    categories = result.scalars().all()

    return categories, total


async def update_category(
    session: SessionDep, category_id: uuid.UUID, category_data: CategoryUpdate
) -> Category | None:
    category = await get_category_by_id(session, category_id)
    if not category:
        return None

    if category_data.slug is not None:
        existing = await get_category_by_slug(session, category_data.slug)
        if existing and existing.id != category_id:
            raise ValueError(f"Category with slug '{category_data.slug}' already exists")

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
    except IntegrityError as err:
        await session.rollback()

        if category_data.slug is not None:
            raise ValueError(f"Category with slug '{category_data.slug}' already exists") from err
        raise ValueError("Database integrity constraint violation") from err
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
