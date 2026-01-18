import uuid

import pytest
from httpx import AsyncClient


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
    payload = {}
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
    payload = {}
    response = await client.post("/api/v1/orders/", json=payload, headers=headers)
    # Should fail because cart is empty
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
