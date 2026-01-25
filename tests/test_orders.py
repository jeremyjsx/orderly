import uuid

import pytest
from httpx import AsyncClient

from app.modules.users.models import User

SHIPPING_ADDRESS = {
    "recipient_name": "John Doe",
    "phone": "+1234567890",
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA",
}


@pytest.mark.asyncio
async def test_create_order_requires_auth(client: AsyncClient):
    """Test that creating an order requires authentication."""
    payload = {}
    response = await client.post("/api/v1/orders/", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_order_no_cart(client: AsyncClient, user_token: str):
    """Test creating an order with no active cart."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"shipping_address": SHIPPING_ADDRESS}
    response = await client.post("/api/v1/orders/", json=payload, headers=headers)
    assert response.status_code == 400
    assert "No active cart found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_order_empty_cart(
    client: AsyncClient, user_token: str, db_session
):
    """Test creating an order with empty cart."""
    from app.modules.cart.models import Cart
    from app.modules.users.models import User

    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()

    cart = Cart(id=uuid.uuid4(), user_id=user.id)
    db_session.add(cart)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"shipping_address": SHIPPING_ADDRESS}
    response = await client.post("/api/v1/orders/", json=payload, headers=headers)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_orders_requires_auth(client: AsyncClient):
    """Test that listing orders requires authentication."""
    response = await client.get("/api/v1/orders/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_all_orders_requires_admin(client: AsyncClient):
    """Test that listing all orders requires admin role."""
    response = await client.get("/api/v1/orders/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_all_orders_requires_admin_role(
    client: AsyncClient, user_token: str
):
    """Test that regular users cannot list all orders."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await client.get("/api/v1/orders/", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_order_requires_auth(client: AsyncClient):
    """Test that getting an order requires authentication."""
    order_id = uuid.uuid4()
    response = await client.get(f"/api/v1/orders/{order_id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cancel_order_requires_auth(client: AsyncClient):
    """Test that canceling an order requires authentication."""
    order_id = uuid.uuid4()
    response = await client.patch(f"/api/v1/orders/{order_id}/cancel")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_order_status_requires_admin(client: AsyncClient):
    """Test that updating order status requires admin role."""
    order_id = uuid.uuid4()
    payload = {"status": "processing"}
    response = await client.patch(f"/api/v1/orders/{order_id}/status", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_order_status_requires_admin_role(
    client: AsyncClient, user_token: str
):
    """Test that regular users cannot update order status."""
    headers = {"Authorization": f"Bearer {user_token}"}
    order_id = uuid.uuid4()
    payload = {"status": "processing"}
    response = await client.patch(
        f"/api/v1/orders/{order_id}/status", json=payload, headers=headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_order_success(client: AsyncClient, user_token: str, db_session):
    """Test successfully creating an order from cart."""
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
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 2},
        headers=headers,
    )

    payload = {"shipping_address": SHIPPING_ADDRESS}
    response = await client.post("/api/v1/orders/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["total"] == 21.98
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["product_id"] == str(product.id)
    assert data["shipping_address"] is not None
    assert data["shipping_address"]["recipient_name"] == "John Doe"

    cart_response = await client.get("/api/v1/cart/me", headers=headers)
    assert cart_response.status_code == 200
    cart_data = cart_response.json()
    assert len(cart_data["items"]) == 0


@pytest.mark.asyncio
async def test_assign_driver_requires_auth(client: AsyncClient):
    """Test that assigning driver requires authentication."""
    order_id = uuid.uuid4()
    response = await client.patch(f"/api/v1/orders/{order_id}/assign")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_assign_driver_to_order_success(
    client: AsyncClient, driver_token: str, test_user: User, db_session
):
    """Test successfully assigning a driver to an order."""
    from app.modules.orders.models import Order, OrderStatus

    order = Order(
        id=uuid.uuid4(),
        user_id=test_user.id,
        status=OrderStatus.PENDING.value,
        total=100.0,
    )
    db_session.add(order)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {driver_token}"}
    response = await client.patch(f"/api/v1/orders/{order.id}/assign", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["driver_id"] is not None
    assert data["id"] == str(order.id)


@pytest.mark.asyncio
async def test_list_available_orders_requires_driver(
    client: AsyncClient, user_token: str
):
    """Test that listing available orders requires DRIVER role."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await client.get("/api/v1/orders/available", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_available_orders(
    client: AsyncClient,
    driver_token: str,
    test_user: User,
    test_driver: User,
    db_session,
):
    """Test listing available orders for drivers."""
    from app.modules.orders.models import Order, OrderStatus

    order1 = Order(
        id=uuid.uuid4(),
        user_id=test_user.id,
        status=OrderStatus.PENDING.value,
        total=100.0,
        driver_id=None,
    )

    order2 = Order(
        id=uuid.uuid4(),
        user_id=test_user.id,
        status=OrderStatus.PROCESSING.value,
        total=200.0,
        driver_id=None,
    )

    order3 = Order(
        id=uuid.uuid4(),
        user_id=test_user.id,
        status=OrderStatus.PENDING.value,
        total=300.0,
        driver_id=test_driver.id,
    )

    db_session.add_all([order1, order2, order3])
    await db_session.commit()

    headers = {"Authorization": f"Bearer {driver_token}"}
    response = await client.get("/api/v1/orders/available", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    order_ids = [item["id"] for item in data["items"]]
    assert str(order1.id) in order_ids
    assert str(order2.id) in order_ids
    assert str(order3.id) not in order_ids


@pytest.mark.asyncio
async def test_list_my_deliveries(
    client: AsyncClient,
    driver_token: str,
    test_driver: User,
    test_user: User,
    db_session,
):
    """Test listing driver's assigned orders."""
    from app.core.security import hash_password
    from app.modules.orders.models import Order, OrderStatus
    from app.modules.users.models import Role, User

    order1 = Order(
        id=uuid.uuid4(),
        user_id=test_user.id,
        status=OrderStatus.PROCESSING.value,
        total=100.0,
        driver_id=test_driver.id,
    )

    order2 = Order(
        id=uuid.uuid4(),
        user_id=test_user.id,
        status=OrderStatus.SHIPPED.value,
        total=200.0,
        driver_id=test_driver.id,
    )

    other_driver = User(
        id=uuid.uuid4(),
        email="otherdriver@example.com",
        hashed_password=hash_password("password123"),
        role=Role.DRIVER.value,
    )
    db_session.add(other_driver)
    await db_session.flush()

    order3 = Order(
        id=uuid.uuid4(),
        user_id=test_user.id,
        status=OrderStatus.PENDING.value,
        total=300.0,
        driver_id=other_driver.id,
    )

    db_session.add_all([order1, order2, order3])
    await db_session.commit()

    headers = {"Authorization": f"Bearer {driver_token}"}
    response = await client.get("/api/v1/orders/my-deliveries", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    order_ids = [item["id"] for item in data["items"]]
    assert str(order1.id) in order_ids
    assert str(order2.id) in order_ids
    assert str(order3.id) not in order_ids


@pytest.mark.asyncio
async def test_assign_driver_order_already_assigned(
    client: AsyncClient,
    driver_token: str,
    test_user: User,
    test_driver: User,
    db_session,
):
    """Test that assigning driver fails when order already has a driver."""
    from app.core.security import hash_password
    from app.modules.orders.models import Order, OrderStatus
    from app.modules.users.models import Role, User

    existing_driver = User(
        id=uuid.uuid4(),
        email="existingdriver@example.com",
        hashed_password=hash_password("password123"),
        role=Role.DRIVER.value,
    )
    db_session.add(existing_driver)
    await db_session.flush()

    order = Order(
        id=uuid.uuid4(),
        user_id=test_user.id,
        status=OrderStatus.PENDING.value,
        total=100.0,
        driver_id=existing_driver.id,
    )
    db_session.add(order)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {driver_token}"}
    response = await client.patch(f"/api/v1/orders/{order.id}/assign", headers=headers)

    assert response.status_code == 400
    assert "already has a driver assigned" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_assign_driver_invalid_status(
    client: AsyncClient, driver_token: str, test_user: User, db_session
):
    """Test that assigning driver fails when order is in invalid status."""
    from app.modules.orders.models import Order, OrderStatus

    order = Order(
        id=uuid.uuid4(),
        user_id=test_user.id,
        status=OrderStatus.SHIPPED.value,
        total=100.0,
        driver_id=None,
    )
    db_session.add(order)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {driver_token}"}
    response = await client.patch(f"/api/v1/orders/{order.id}/assign", headers=headers)

    assert response.status_code == 400
    assert "not in a valid status" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(
    client: AsyncClient, user_token: str, db_session
):
    """Test creating order fails when product has insufficient stock."""
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
        stock=5,
        category_id=category.id,
        image_url="https://example.com/image.jpg",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {user_token}"}

    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 3},
        headers=headers,
    )

    product.stock = 2
    await db_session.commit()

    payload = {"shipping_address": SHIPPING_ADDRESS}
    response = await client.post("/api/v1/orders/", json=payload, headers=headers)
    assert response.status_code == 400
    assert "insufficient stock" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_order_inactive_product(
    client: AsyncClient, user_token: str, db_session
):
    """Test creating order fails when cart contains inactive product."""
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
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 2},
        headers=headers,
    )

    product.is_active = False
    await db_session.commit()

    payload = {"shipping_address": SHIPPING_ADDRESS}
    response = await client.post("/api/v1/orders/", json=payload, headers=headers)
    assert response.status_code == 400
    assert "not active" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_my_orders_success(client: AsyncClient, user_token: str, db_session):
    """Test successfully listing user's own orders."""
    from app.modules.categories.models import Category
    from app.modules.orders.models import Order, OrderItem, OrderStatus
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
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=headers,
    )
    order_response = await client.post(
        "/api/v1/orders/",
        json={"shipping_address": SHIPPING_ADDRESS},
        headers=headers,
    )
    assert order_response.status_code == 201

    response = await client.get("/api/v1/orders/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    order_ids = [order["id"] for order in data["items"]]
    assert order_response.json()["id"] in order_ids


@pytest.mark.asyncio
async def test_get_order_success(client: AsyncClient, user_token: str, db_session):
    """Test successfully getting an order."""
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
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 2},
        headers=headers,
    )
    order_response = await client.post(
        "/api/v1/orders/",
        json={"shipping_address": SHIPPING_ADDRESS},
        headers=headers,
    )
    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    response = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id
    assert data["status"] == "pending"
    assert data["total"] == 21.98
    assert len(data["items"]) == 1
    assert data["shipping_address"] is not None


@pytest.mark.asyncio
async def test_get_order_forbidden(client: AsyncClient, user_token: str, db_session):
    """Test that users cannot view other users' orders."""
    from app.core.security import hash_password
    from app.modules.cart.models import Cart, CartItem
    from app.modules.categories.models import Category
    from app.modules.orders.models import Order, OrderItem, OrderStatus
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

    other_order = Order(
        id=uuid.uuid4(),
        user_id=other_user.id,
        status=OrderStatus.PENDING.value,
        total=10.99,
    )
    db_session.add(other_order)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {user_token}"}
    response = await client.get(f"/api/v1/orders/{other_order.id}", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cancel_order_success(client: AsyncClient, user_token: str, db_session):
    """Test successfully canceling an order."""
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
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=headers,
    )
    order_response = await client.post(
        "/api/v1/orders/",
        json={"shipping_address": SHIPPING_ADDRESS},
        headers=headers,
    )
    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    response = await client.patch(f"/api/v1/orders/{order_id}/cancel", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_order_forbidden(client: AsyncClient, user_token: str, db_session):
    """Test that users cannot cancel other users' orders."""
    from app.core.security import hash_password
    from app.modules.cart.models import Cart, CartItem
    from app.modules.categories.models import Category
    from app.modules.orders.models import Order, OrderStatus
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

    other_order = Order(
        id=uuid.uuid4(),
        user_id=other_user.id,
        status=OrderStatus.PENDING.value,
        total=10.99,
    )
    db_session.add(other_order)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {user_token}"}
    response = await client.patch(
        f"/api/v1/orders/{other_order.id}/cancel", headers=headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_order_status_success(
    client: AsyncClient, admin_token: str, db_session
):
    """Test successfully updating order status."""
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

    from app.core.security import create_access_token, hash_password
    from app.modules.users.models import User

    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    user_token = create_access_token(user.id)

    user_headers = {"Authorization": f"Bearer {user_token}"}
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=user_headers,
    )
    order_response = await client.post(
        "/api/v1/orders/",
        json={"shipping_address": SHIPPING_ADDRESS},
        headers=user_headers,
    )
    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"status": "processing"}
    response = await client.patch(
        f"/api/v1/orders/{order_id}/status", json=payload, headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"


@pytest.mark.asyncio
async def test_update_order_status_invalid_transition(
    client: AsyncClient, admin_token: str, db_session
):
    """Test that invalid status transitions are rejected."""
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

    from app.core.security import create_access_token, hash_password
    from app.modules.users.models import User

    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    user_token = create_access_token(user.id)

    user_headers = {"Authorization": f"Bearer {user_token}"}
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=user_headers,
    )
    order_response = await client.post(
        "/api/v1/orders/",
        json={"shipping_address": SHIPPING_ADDRESS},
        headers=user_headers,
    )
    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"status": "delivered"}
    response = await client.patch(
        f"/api/v1/orders/{order_id}/status", json=payload, headers=admin_headers
    )
    assert response.status_code == 400
    assert "transition" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_all_orders_success(
    client: AsyncClient, admin_token: str, db_session
):
    """Test successfully listing all orders as admin."""
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

    from app.core.security import create_access_token, hash_password
    from app.modules.users.models import User

    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    user_token = create_access_token(user.id)

    user_headers = {"Authorization": f"Bearer {user_token}"}
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=user_headers,
    )
    order_response = await client.post(
        "/api/v1/orders/",
        json={"shipping_address": SHIPPING_ADDRESS},
        headers=user_headers,
    )
    assert order_response.status_code == 201

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/api/v1/orders/", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
