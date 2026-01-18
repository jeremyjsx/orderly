import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_product_requires_admin(client: AsyncClient):
    """Test that creating a product requires admin role."""
    payload = {
        "name": "Test Product",
        "description": "Test description",
        "price": 10.99,
        "stock": 100,
        "category_id": str(uuid.uuid4()),
        "image_url": "https://example.com/image.jpg",
    }
    response = await client.post("/api/v1/products/", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_product_requires_admin_role(client: AsyncClient, user_token: str):
    """Test that regular users cannot create products."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "name": "Test Product",
        "description": "Test description",
        "price": 10.99,
        "stock": 100,
        "category_id": str(uuid.uuid4()),
        "image_url": "https://example.com/image.jpg",
    }
    response = await client.post("/api/v1/products/", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_product_success(
    client: AsyncClient, admin_token: str, db_session
):
    """Test successful product creation by admin."""
    from app.modules.categories.models import Category

    # Create a category first
    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test category description",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "Test Product",
        "description": "Test description",
        "price": 10.99,
        "stock": 100,
        "category_id": str(category.id),
        "image_url": "https://example.com/image.jpg",
    }
    response = await client.post("/api/v1/products/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["price"] == 10.99
    assert data["stock"] == 100
    assert data["category_id"] == str(category.id)


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient):
    """Test getting a non-existent product."""
    product_id = uuid.uuid4()
    response = await client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_products_empty(client: AsyncClient):
    """Test listing products when there are none."""
    response = await client.get("/api/v1/products/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["has_more"] is False


@pytest.mark.asyncio
async def test_list_products_with_items(
    client: AsyncClient, admin_token: str, db_session
):
    """Test listing products with items."""
    from app.modules.categories.models import Category
    from app.modules.products.models import Product

    # Create category and products
    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    product1 = Product(
        id=uuid.uuid4(),
        name="Product 1",
        description="Description 1",
        price=10.99,
        stock=100,
        category_id=category.id,
        image_url="https://example.com/1.jpg",
        is_active=True,
    )
    product2 = Product(
        id=uuid.uuid4(),
        name="Product 2",
        description="Description 2",
        price=20.99,
        stock=50,
        category_id=category.id,
        image_url="https://example.com/2.jpg",
        is_active=True,
    )
    db_session.add_all([product1, product2])
    await db_session.commit()

    response = await client.get("/api/v1/products/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_update_product_requires_admin(client: AsyncClient, db_session):
    """Test that updating a product requires admin role."""
    from app.modules.categories.models import Category
    from app.modules.products.models import Product

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    product = Product(
        id=uuid.uuid4(),
        name="Test Product",
        description="Test",
        price=10.99,
        stock=100,
        category_id=category.id,
        image_url="https://example.com/image.jpg",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    payload = {"name": "Updated Product"}
    response = await client.patch(f"/api/v1/products/{product.id}", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_product_requires_admin(client: AsyncClient, db_session):
    """Test that deleting a product requires admin role."""
    from app.modules.categories.models import Category
    from app.modules.products.models import Product

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    product = Product(
        id=uuid.uuid4(),
        name="Test Product",
        description="Test",
        price=10.99,
        stock=100,
        category_id=category.id,
        image_url="https://example.com/image.jpg",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    response = await client.delete(f"/api/v1/products/{product.id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_product_success(
    client: AsyncClient, admin_token: str, db_session
):
    """Test successfully updating a product."""
    from app.modules.categories.models import Category
    from app.modules.products.models import Product

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    product = Product(
        id=uuid.uuid4(),
        name="Test Product",
        description="Test",
        price=10.99,
        stock=100,
        category_id=category.id,
        image_url="https://example.com/image.jpg",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "Updated Product",
        "price": 15.99,
        "stock": 50,
    }
    response = await client.patch(
        f"/api/v1/products/{product.id}", json=payload, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Product"
    assert data["price"] == 15.99
    assert data["stock"] == 50
    assert data["id"] == str(product.id)


@pytest.mark.asyncio
async def test_delete_product_success(
    client: AsyncClient, admin_token: str, db_session
):
    """Test successfully deleting a product."""
    from app.modules.categories.models import Category
    from app.modules.products.models import Product

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    product = Product(
        id=uuid.uuid4(),
        name="Test Product",
        description="Test",
        price=10.99,
        stock=100,
        category_id=category.id,
        image_url="https://example.com/image.jpg",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.delete(f"/api/v1/products/{product.id}", headers=headers)
    assert response.status_code == 204

    # Verify product is deleted
    get_response = await client.get(f"/api/v1/products/{product.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_product_inactive_category(
    client: AsyncClient, admin_token: str, db_session
):
    """Test that products cannot be created in inactive categories."""
    from app.modules.categories.models import Category

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
        is_active=False,  # Inactive category
    )
    db_session.add(category)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "Test Product",
        "description": "Test description",
        "price": 10.99,
        "stock": 100,
        "category_id": str(category.id),
        "image_url": "https://example.com/image.jpg",
    }
    response = await client.post("/api/v1/products/", json=payload, headers=headers)
    assert response.status_code == 400
    assert "inactive category" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_product_success(client: AsyncClient, db_session):
    """Test successfully getting a product by ID."""
    from app.modules.categories.models import Category
    from app.modules.products.models import Product

    category = Category(
        id=uuid.uuid4(),
        name="Test Category",
        description="Test",
        slug="test-category",
    )
    db_session.add(category)
    await db_session.commit()

    product = Product(
        id=uuid.uuid4(),
        name="Test Product",
        description="Test Description",
        price=10.99,
        stock=100,
        category_id=category.id,
        image_url="https://example.com/image.jpg",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    response = await client.get(f"/api/v1/products/{product.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(product.id)
    assert data["name"] == "Test Product"
    assert data["price"] == 10.99
    assert data["stock"] == 100
