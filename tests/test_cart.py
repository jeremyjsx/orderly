import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_cart_requires_auth(client: AsyncClient):
    """Test that getting cart requires authentication."""
    response = await client.get("/api/v1/cart/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_empty_cart(client: AsyncClient, user_token: str):
    """Test getting an empty cart."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await client.get("/api/v1/cart/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["totals"]["subtotal"] == 0.0
    assert data["totals"]["total_items"] == 0
    assert data["totals"]["total_quantity"] == 0


@pytest.mark.asyncio
async def test_add_item_to_cart_requires_auth(client: AsyncClient, db_session):
    """Test that adding item to cart requires authentication."""
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

    payload = {"product_id": str(product.id), "quantity": 1}
    response = await client.post("/api/v1/cart/items", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_add_item_to_cart_success(
    client: AsyncClient, user_token: str, db_session
):
    """Test successfully adding an item to cart."""
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

    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"product_id": str(product.id), "quantity": 2}
    response = await client.post("/api/v1/cart/items", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["product"]["id"] == str(product.id)
    assert data["quantity"] == 2
    assert data["subtotal"] == 21.98  # 2 * 10.99


@pytest.mark.asyncio
async def test_add_item_to_cart_product_not_found(client: AsyncClient, user_token: str):
    """Test adding a non-existent product to cart."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"product_id": str(uuid.uuid4()), "quantity": 1}
    response = await client.post("/api/v1/cart/items", json=payload, headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_cart_item_requires_auth(client: AsyncClient, db_session):
    """Test that updating cart item requires authentication."""
    from app.modules.cart.models import Cart, CartItem
    from app.modules.categories.models import Category
    from app.modules.products.models import Product
    from app.modules.users.models import User

    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()

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

    cart = Cart(id=uuid.uuid4(), user_id=user.id)
    db_session.add(cart)
    await db_session.commit()

    cart_item = CartItem(
        id=uuid.uuid4(), cart_id=cart.id, product_id=product.id, quantity=1
    )
    db_session.add(cart_item)
    await db_session.commit()

    payload = {"quantity": 3}
    response = await client.put(f"/api/v1/cart/items/{cart_item.id}", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_cart_item_requires_auth(client: AsyncClient, db_session):
    """Test that deleting cart item requires authentication."""
    from app.modules.cart.models import Cart, CartItem
    from app.modules.categories.models import Category
    from app.modules.products.models import Product
    from app.modules.users.models import User

    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()

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

    cart = Cart(id=uuid.uuid4(), user_id=user.id)
    db_session.add(cart)
    await db_session.commit()

    cart_item = CartItem(
        id=uuid.uuid4(), cart_id=cart.id, product_id=product.id, quantity=1
    )
    db_session.add(cart_item)
    await db_session.commit()

    response = await client.delete(f"/api/v1/cart/items/{cart_item.id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_clear_cart_requires_auth(client: AsyncClient):
    """Test that clearing cart requires authentication."""
    response = await client.delete("/api/v1/cart/")
    assert response.status_code == 401
