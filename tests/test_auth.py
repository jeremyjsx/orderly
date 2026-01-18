import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Test successful user registration."""
    payload = {
        "email": "newuser@example.com",
        "password": "password123",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "password" not in data
    assert "id" in data
    assert "role" in data
    assert data["role"] == "user"


@pytest.mark.asyncio
async def test_register_user_duplicate_email(client: AsyncClient, test_user: None):
    """Test registration with duplicate email."""
    payload = {
        "email": "test@example.com",
        "password": "password123",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_user_invalid_email(client: AsyncClient):
    """Test registration with invalid email."""
    payload = {
        "email": "invalid-email",
        "password": "password123",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_user_short_password(client: AsyncClient):
    """Test registration with password too short."""
    payload = {
        "email": "user@example.com",
        "password": "short",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: None):
    """Test successful login."""
    payload = {
        "email": "test@example.com",
        "password": "testpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials."""
    payload = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: None):
    """Test login with wrong password."""
    payload = {
        "email": "test@example.com",
        "password": "wrongpassword",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
