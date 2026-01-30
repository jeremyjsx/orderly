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
    assert data["image_url"] is None


@pytest.mark.asyncio
async def test_create_category_duplicate_slug(client: AsyncClient, admin_token: str):
    """Test creating a category with duplicate slug."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "Test Category",
        "description": "Test description",
        "slug": "test-category",
    }
    response1 = await client.post("/api/v1/categories/", json=payload, headers=headers)
    assert response1.status_code == 201

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


@pytest.mark.asyncio
async def test_get_category_success(client: AsyncClient, admin_token: str, db_session):
    """Test successfully getting a category by ID."""
    from app.modules.categories.models import Category

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test Description",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    response = await client.get(f"/api/v1/categories/{category.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(category.id)
    assert data["name"] == "Test Category"
    assert data["slug"] == "test-category"


@pytest.mark.asyncio
async def test_get_category_by_slug_success(
    client: AsyncClient, admin_token: str, db_session
):
    """Test successfully getting a category by slug."""
    from app.modules.categories.models import Category

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test Description",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    response = await client.get("/api/v1/categories/slug/test-category")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(category.id)
    assert data["name"] == "Test Category"
    assert data["slug"] == "test-category"


@pytest.mark.asyncio
async def test_update_category_success(
    client: AsyncClient, admin_token: str, db_session
):
    """Test successfully updating a category."""
    from app.modules.categories.models import Category

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "Updated Category",
        "description": "Updated Description",
    }
    response = await client.patch(
        f"/api/v1/categories/{category.id}", json=payload, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Category"
    assert data["description"] == "Updated Description"
    assert data["id"] == str(category.id)


@pytest.mark.asyncio
async def test_delete_category_success(
    client: AsyncClient, admin_token: str, db_session, mock_s3_upload
):
    """Test successfully deleting a category."""
    from app.modules.categories.models import Category

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.delete(f"/api/v1/categories/{category.id}", headers=headers)
    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/categories/{category.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_categories_with_items(
    client: AsyncClient, admin_token: str, db_session
):
    """Test listing categories with items."""
    from app.modules.categories.models import Category

    category1 = Category(
        id=uuid.uuid4(),
        name="Category 1",
        description="Description 1",
        slug="category-1",
    )
    category2 = Category(
        id=uuid.uuid4(),
        name="Category 2",
        description="Description 2",
        slug="category-2",
    )
    db_session.add_all([category1, category2])
    await db_session.commit()

    response = await client.get("/api/v1/categories/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
    category_names = [cat["name"] for cat in data["items"]]
    assert "Category 1" in category_names
    assert "Category 2" in category_names


@pytest.mark.asyncio
async def test_upload_category_image_success(
    client: AsyncClient, admin_token: str, db_session, mock_s3_upload, test_image_file
):
    """Test that an admin can upload an image to a category."""
    from app.modules.categories.models import Category

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    filename, file_content, content_type = test_image_file
    files = {"image": (filename, file_content, content_type)}

    response = await client.put(
        f"/api/v1/categories/{category.id}/image", files=files, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image_url"] is not None


@pytest.mark.asyncio
async def test_upload_category_image_not_found(
    client: AsyncClient, admin_token: str, mock_s3_upload, test_image_file
):
    """Test that uploading an image to a non-existent category returns 404."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    filename, file_content, content_type = test_image_file
    files = {"image": (filename, file_content, content_type)}

    response = await client.put(
        f"/api/v1/categories/{uuid.uuid4()}/image", files=files, headers=headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_image_success(
    client: AsyncClient, admin_token: str, db_session, mock_s3_upload
):
    """Test that an admin can delete a category image."""
    from app.modules.categories.models import Category

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
        image_url="https://example.com/image.jpg",
    )
    db_session.add(category)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.delete(
        f"/api/v1/categories/{category.id}/image", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image_url"] is None


@pytest.mark.asyncio
async def test_delete_category_image_no_image(
    client: AsyncClient, admin_token: str, db_session
):
    """Test that deleting an image from a category without one returns 404."""
    from app.modules.categories.models import Category

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.delete(
        f"/api/v1/categories/{category.id}/image", headers=headers
    )
    assert response.status_code == 404
