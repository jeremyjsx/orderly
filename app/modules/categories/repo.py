import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.redis import cache_key, delete_cache, get_cache, set_cache
from app.db.session import SessionDep
from app.modules.categories.models import Category
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate


def _category_to_dict(category: Category) -> dict:
    """Convert Category model to dict for caching."""
    return {
        "id": str(category.id),
        "name": category.name,
        "description": category.description,
        "slug": category.slug,
        "is_active": category.is_active,
        "image_url": category.image_url,
    }


async def _invalidate_category_cache(category_id: uuid.UUID | None = None) -> None:
    """Invalidate category caches."""
    await delete_cache("categories")
    if category_id:
        await delete_cache(f"category:{category_id}")


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
        raise ValueError(
            f"Category with slug '{category_data.slug}' already exists"
        ) from err
    await session.refresh(category)
    await _invalidate_category_cache()
    return category


async def get_category_by_id(
    session: SessionDep, category_id: uuid.UUID
) -> Category | None:
    key = cache_key("category", str(category_id))
    cached = await get_cache(key)
    if cached:
        result = await session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    result = await session.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()

    if category:
        await set_cache(
            key, _category_to_dict(category), ttl=settings.CACHE_TTL_CATEGORY
        )

    return category


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
            raise ValueError(
                f"Category with slug '{category_data.slug}' already exists"
            )

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
            raise ValueError(
                f"Category with slug '{category_data.slug}' already exists"
            ) from err
        raise ValueError("Database integrity constraint violation") from err
    await _invalidate_category_cache(category_id)
    return category


async def update_category_image(
    session: SessionDep, category_id: uuid.UUID, image_url: str | None
) -> Category | None:
    category = await get_category_by_id(session, category_id)
    if not category:
        return None

    category.image_url = image_url
    await session.commit()
    await session.refresh(category)
    await _invalidate_category_cache(category_id)
    return category


async def delete_category(session: SessionDep, category_id: uuid.UUID) -> bool:
    category = await get_category_by_id(session, category_id)
    if not category:
        return False

    try:
        await session.delete(category)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    await _invalidate_category_cache(category_id)
    return True
