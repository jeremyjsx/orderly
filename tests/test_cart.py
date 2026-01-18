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


@pytest.mark.asyncio
async def test_get_cart_with_items(client: AsyncClient, user_token: str, db_session):
    """Test getting cart with items."""
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

    product1 = Product(
        id=uuid.uuid4(),
        name="Product 1",
        description="Test",
        price=10.99,
        stock=100,
        category_id=category.id,
        image_url="https://example.com/1.jpg",
        is_active=True,
    )
    product2 = Product(
        id=uuid.uuid4(),
        name="Product 2",
        description="Test",
        price=20.50,
        stock=50,
        category_id=category.id,
        image_url="https://example.com/2.jpg",
        is_active=True,
    )
    db_session.add_all([product1, product2])
    await db_session.commit()

    headers = {"Authorization": f"Bearer {user_token}"}
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product1.id), "quantity": 2},
        headers=headers,
    )
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product2.id), "quantity": 1},
        headers=headers,
    )

    response = await client.get("/api/v1/cart/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert abs(data["totals"]["subtotal"] - 42.48) < 0.01  # (2 * 10.99) + (1 * 20.50)
    assert data["totals"]["total_items"] == 2
    assert data["totals"]["total_quantity"] == 3


@pytest.mark.asyncio
async def test_update_cart_item_success(
    client: AsyncClient, user_token: str, db_session
):
    """Test successfully updating cart item quantity."""
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
    add_response = await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 2},
        headers=headers,
    )
    assert add_response.status_code == 201
    item_id = add_response.json()["id"]

    payload = {"quantity": 5}
    response = await client.put(
        f"/api/v1/cart/items/{item_id}", json=payload, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 5
    assert data["subtotal"] == 54.95  # 5 * 10.99


@pytest.mark.asyncio
async def test_delete_cart_item_success(
    client: AsyncClient, user_token: str, db_session
):
    """Test successfully deleting cart item."""
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
    add_response = await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 2},
        headers=headers,
    )
    assert add_response.status_code == 201
    item_id = add_response.json()["id"]

    response = await client.delete(f"/api/v1/cart/items/{item_id}", headers=headers)
    assert response.status_code == 204

    # Verify cart is empty
    cart_response = await client.get("/api/v1/cart/me", headers=headers)
    assert cart_response.status_code == 200
    cart_data = cart_response.json()
    assert len(cart_data["items"]) == 0


@pytest.mark.asyncio
async def test_clear_cart_success(client: AsyncClient, user_token: str, db_session):
    """Test successfully clearing cart."""
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
    # Add items to cart
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 2},
        headers=headers,
    )

    cart_before = await client.get("/api/v1/cart/me", headers=headers)
    assert cart_before.status_code == 200
    assert len(cart_before.json()["items"]) == 1

    response = await client.delete("/api/v1/cart/", headers=headers)
    assert response.status_code == 204

    await db_session.commit()

    cart_response = await client.get("/api/v1/cart/me", headers=headers)
    assert cart_response.status_code == 200
    cart_data = cart_response.json()
    assert len(cart_data["items"]) == 0


@pytest.mark.asyncio
async def test_add_item_to_cart_inactive_product(
    client: AsyncClient, user_token: str, db_session
):
    """Test that inactive products cannot be added to cart."""
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
        is_active=False,  # Inactive product
    )
    db_session.add(product)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"product_id": str(product.id), "quantity": 1}
    response = await client.post("/api/v1/cart/items", json=payload, headers=headers)
    assert response.status_code == 400
    assert "not active" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_add_item_to_cart_insufficient_stock(
    client: AsyncClient, user_token: str, db_session
):
    """Test that items cannot be added to cart if stock is insufficient."""
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
        stock=5,  # Limited stock
        category_id=category.id,
        image_url="https://example.com/image.jpg",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"product_id": str(product.id), "quantity": 10}  # More than stock
    response = await client.post("/api/v1/cart/items", json=payload, headers=headers)
    assert response.status_code == 400
    assert "insufficient stock" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_cart_item_insufficient_stock(
    client: AsyncClient, user_token: str, db_session
):
    """Test that cart item cannot be updated if new quantity exceeds stock."""
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
        stock=5,  # Limited stock
        category_id=category.id,
        image_url="https://example.com/image.jpg",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {user_token}"}
    add_response = await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 2},
        headers=headers,
    )
    assert add_response.status_code == 201
    item_id = add_response.json()["id"]

    payload = {"quantity": 10}
    response = await client.put(
        f"/api/v1/cart/items/{item_id}", json=payload, headers=headers
    )
    assert response.status_code == 400
    assert "insufficient stock" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_cart_item_forbidden(
    client: AsyncClient, user_token: str, db_session
):
    """Test that users cannot update cart items from other users' carts."""
    from app.core.security import create_access_token, hash_password
    from app.modules.cart.models import Cart, CartItem
    from app.modules.categories.models import Category
    from app.modules.products.models import Product
    from app.modules.users.models import User

    other_user = User(
        id=uuid.uuid4(),
        email="other@example.com",
        hashed_password=hash_password("password123"),
    )
    db_session.add(other_user)
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

    other_cart = Cart(id=uuid.uuid4(), user_id=other_user.id)
    db_session.add(other_cart)
    await db_session.commit()

    cart_item = CartItem(
        id=uuid.uuid4(),
        cart_id=other_cart.id,
        product_id=product.id,
        quantity=1,
    )
    db_session.add(cart_item)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"quantity": 3}
    response = await client.put(
        f"/api/v1/cart/items/{cart_item.id}", json=payload, headers=headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_cart_item_forbidden(
    client: AsyncClient, user_token: str, db_session
):
    """Test that users cannot delete cart items from other users' carts."""
    from app.core.security import hash_password
    from app.modules.cart.models import Cart, CartItem
    from app.modules.categories.models import Category
    from app.modules.products.models import Product
    from app.modules.users.models import User

    other_user = User(
        id=uuid.uuid4(),
        email="other@example.com",
        hashed_password=hash_password("password123"),
    )
    db_session.add(other_user)
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

    other_cart = Cart(id=uuid.uuid4(), user_id=other_user.id)
    db_session.add(other_cart)
    await db_session.commit()

    cart_item = CartItem(
        id=uuid.uuid4(),
        cart_id=other_cart.id,
        product_id=product.id,
        quantity=1,
    )
    db_session.add(cart_item)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {user_token}"}
    response = await client.delete(
        f"/api/v1/cart/items/{cart_item.id}", headers=headers
    )
    assert response.status_code == 403
