import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_my_profile_requires_auth(client: AsyncClient):
    """Test that getting own profile requires authentication."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_my_profile_success(client: AsyncClient, user_token: str, test_user):
    """Test successfully getting own profile."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email
    assert data["role"] == "user"


@pytest.mark.asyncio
async def test_change_password_requires_auth(client: AsyncClient):
    """Test that changing password requires authentication."""
    payload = {
        "current_password": "oldpassword123",
        "new_password": "newpassword123",
    }
    response = await client.patch("/api/v1/users/me/password", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_wrong_current_password(
    client: AsyncClient, user_token: str
):
    """Test changing password with incorrect current password."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "current_password": "wrongpassword123",
        "new_password": "newpassword123",
    }
    response = await client.patch(
        "/api/v1/users/me/password", json=payload, headers=headers
    )
    assert response.status_code == 400
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient, user_token: str, test_user):
    """Test successfully changing password."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "current_password": "testpassword123",
        "new_password": "newpassword123",
    }
    response = await client.patch(
        "/api/v1/users/me/password", json=payload, headers=headers
    )
    assert response.status_code == 204

    # Verify new password works by logging in
    login_payload = {"email": test_user.email, "password": "newpassword123"}
    login_response = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_list_users_requires_auth(client: AsyncClient):
    """Test that listing users requires authentication."""
    response = await client.get("/api/v1/users/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_users_requires_admin(client: AsyncClient, user_token: str):
    """Test that listing users requires admin role."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_users_success(
    client: AsyncClient, admin_token: str, test_user, test_admin
):
    """Test successfully listing users as admin."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2  # At least test_user and test_admin
    assert len(data["items"]) >= 2
    user_emails = [user["email"] for user in data["items"]]
    assert test_user.email in user_emails
    assert test_admin.email in user_emails


@pytest.mark.asyncio
async def test_list_users_pagination(client: AsyncClient, admin_token: str, db_session):
    """Test listing users with pagination."""
    from app.core.security import hash_password
    from app.modules.users.models import User

    # Create additional users
    for i in range(5):
        user = User(
            id=uuid.uuid4(),
            email=f"user{i}@example.com",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/api/v1/users/?limit=3&offset=0", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["limit"] == 3
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_get_user_requires_auth(client: AsyncClient, test_user):
    """Test that getting user by ID requires authentication."""
    response = await client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_user_requires_admin(client: AsyncClient, user_token: str, test_user):
    """Test that getting user by ID requires admin role."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await client.get(f"/api/v1/users/{test_user.id}", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient, admin_token: str):
    """Test getting a non-existent user."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_id = uuid.uuid4()
    response = await client.get(f"/api/v1/users/{user_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_success(client: AsyncClient, admin_token: str, test_user):
    """Test successfully getting user by ID as admin."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get(f"/api/v1/users/{test_user.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email
    assert data["role"] == "user"


@pytest.mark.asyncio
async def test_update_user_requires_auth(client: AsyncClient, test_user):
    """Test that updating user requires authentication."""
    payload = {"email": "updated@example.com"}
    response = await client.patch(f"/api/v1/users/{test_user.id}", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_requires_admin(
    client: AsyncClient, user_token: str, test_user
):
    """Test that updating user requires admin role."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"email": "updated@example.com"}
    response = await client.patch(
        f"/api/v1/users/{test_user.id}", json=payload, headers=headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient, admin_token: str):
    """Test updating a non-existent user."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_id = uuid.uuid4()
    payload = {"email": "updated@example.com"}
    response = await client.patch(
        f"/api/v1/users/{user_id}", json=payload, headers=headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_duplicate_email(
    client: AsyncClient, admin_token: str, test_user, test_admin
):
    """Test updating user with duplicate email."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"email": test_admin.email}  # Use admin's email
    response = await client.patch(
        f"/api/v1/users/{test_user.id}", json=payload, headers=headers
    )
    assert response.status_code == 400
    assert "already taken" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_user_success(client: AsyncClient, admin_token: str, test_user):
    """Test successfully updating user as admin."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"email": "updated@example.com"}
    response = await client.patch(
        f"/api/v1/users/{test_user.id}", json=payload, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == "updated@example.com"


@pytest.mark.asyncio
async def test_delete_user_requires_auth(client: AsyncClient, test_user):
    """Test that deleting user requires authentication."""
    response = await client.delete(f"/api/v1/users/{test_user.id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_user_requires_admin(
    client: AsyncClient, user_token: str, test_user
):
    """Test that deleting user requires admin role."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await client.delete(f"/api/v1/users/{test_user.id}", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_cannot_delete_self(
    client: AsyncClient, admin_token: str, test_admin
):
    """Test that admin cannot delete their own account."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.delete(f"/api/v1/users/{test_admin.id}", headers=headers)
    assert response.status_code == 400
    assert "own account" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient, admin_token: str):
    """Test deleting a non-existent user."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_id = uuid.uuid4()
    response = await client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_success(client: AsyncClient, admin_token: str, test_user):
    """Test successfully deleting user as admin."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.delete(f"/api/v1/users/{test_user.id}", headers=headers)
    assert response.status_code == 204

    # Verify user is deleted
    get_response = await client.get(f"/api/v1/users/{test_user.id}", headers=headers)
    assert get_response.status_code == 404
