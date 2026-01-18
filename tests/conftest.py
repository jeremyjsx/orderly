import os
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db import models  # noqa: F401 - Import all models to register them
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.modules.users.models import Role, User

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Create a fresh database session for each test.

    Each test gets a completely fresh database with tables created
    and dropped after the test completes.
    """
    # Create engine for each test to avoid event loop issues
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Avoid event loop issues with connection pooling
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Clean slate
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    session = AsyncSession(bind=engine, expire_on_commit=False)

    try:
        yield session
    finally:
        await session.close()
        # Drop all tables after test
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Create a test client that shares the same database session."""
    app = create_app()

    async def override_get_db():
        """Override to use the same session as the test."""
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user with USER role."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        role=Role.ADMIN.value,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user: User) -> str:
    """Create a JWT token for test user."""
    return create_access_token(test_user.id)


@pytest.fixture
def admin_token(test_admin: User) -> str:
    """Create a JWT token for test admin."""
    return create_access_token(test_admin.id)
