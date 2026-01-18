import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.security import create_access_token
from app.db import models  # noqa: F401 - Import all models to register them
from app.db.base import Base
from app.main import create_app
from app.modules.users.models import Role, User
from app.modules.users.repo import create_user

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="function")
async def setup_database():
    """Create all tables for each test function."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Clean up: drop all tables after each test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test with transaction rollback."""
    async with test_engine.connect() as connection:
        trans = await connection.begin()
        async with TestSessionLocal(bind=connection) as session:
            yield session
            await trans.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database override."""
    app = create_app()

    async def override_get_db():
        yield db_session

    from app.db.session import get_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user with USER role."""
    return await create_user(db_session, "test@example.com", "testpassword123")


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    user = await create_user(db_session, "admin@example.com", "adminpassword123")
    user.role = Role.ADMIN.value
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
