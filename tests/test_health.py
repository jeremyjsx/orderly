import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test basic health check endpoint."""
    response = await client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_db_requires_auth(client: AsyncClient):
    """Test that health/db endpoint requires authentication."""
    response = await client.get("/health/db")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_db_requires_admin(client: AsyncClient, user_token: str):
    """Test that health/db endpoint requires admin role."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await client.get("/health/db", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_health_db_success(client: AsyncClient, admin_token: str):
    """Test successful health/db check as admin."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/health/db", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
