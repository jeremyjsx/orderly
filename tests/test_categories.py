import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category_requires_admin(client: AsyncClient):
    """Test that creating a category requires admin role."""
    payload = {
        "name": "Test Category",
        "description": "Test description",
        "slug": "test-category",
    }
    response = await client.post("/api/v1/categories/", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_category_requires_admin_role(
    client: AsyncClient, user_token: str
):
    """Test that regular users cannot create categories."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "name": "Test Category",
        "description": "Test description",
        "slug": "test-category",
    }
    response = await client.post("/api/v1/categories/", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_category_success(client: AsyncClient, admin_token: str):
    """Test successful category creation by admin."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "Test Category",
        "description": "Test description",
        "slug": "test-category",
    }
    response = await client.post("/api/v1/categories/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Category"
    assert data["slug"] == "test-category"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_category_duplicate_slug(client: AsyncClient, admin_token: str):
    """Test creating a category with duplicate slug."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "Test Category",
        "description": "Test description",
        "slug": "test-category",
    }
    # Create first category
    response1 = await client.post("/api/v1/categories/", json=payload, headers=headers)
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = await client.post("/api/v1/categories/", json=payload, headers=headers)
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_list_categories_empty(client: AsyncClient):
    """Test listing categories when there are none."""
    response = await client.get("/api/v1/categories/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_category_not_found(client: AsyncClient):
    """Test getting a non-existent category."""
    category_id = uuid.uuid4()
    response = await client.get(f"/api/v1/categories/{category_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_category_by_slug_not_found(client: AsyncClient):
    """Test getting a category by slug that doesn't exist."""
    response = await client.get("/api/v1/categories/slug/non-existent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_category_requires_admin(client: AsyncClient, db_session):
    """Test that updating a category requires admin role."""
    from app.modules.categories.models import Category

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    payload = {"name": "Updated Category"}
    response = await client.patch(f"/api/v1/categories/{category.id}", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_category_requires_admin(client: AsyncClient, db_session):
    """Test that deleting a category requires admin role."""
    from app.modules.categories.models import Category

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    response = await client.delete(f"/api/v1/categories/{category.id}")
    assert response.status_code == 401
