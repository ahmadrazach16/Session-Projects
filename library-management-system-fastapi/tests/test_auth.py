"""
Tests for authentication: registration, login, JWT validation, roles.
"""


class TestRegistration:
    def test_register_new_user_success(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "johndoe"
        assert data["role"] == "MEMBER"  # self-registration always creates MEMBER
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_username_fails(self, client):
        payload = {
            "username": "johndoe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "password": "SecurePass123",
        }
        client.post("/api/v1/auth/register", json=payload)

        payload["email"] = "different@example.com"
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409
        assert response.json()["error"] == "ConflictError"

    def test_register_duplicate_email_fails(self, client):
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "user1",
                "email": "shared@example.com",
                "full_name": "User One",
                "password": "SecurePass123",
            },
        )
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "user2",
                "email": "shared@example.com",
                "full_name": "User Two",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == 409

    def test_register_weak_password_rejected(self, client):
        """Password shorter than 8 chars should fail Pydantic validation."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "user1",
                "email": "user1@example.com",
                "full_name": "User One",
                "password": "short",
            },
        )
        assert response.status_code == 422

    def test_register_invalid_email_rejected(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "user1",
                "email": "not-an-email",
                "full_name": "User One",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == 422


class TestLogin:
    def _register(self, client):
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "janedoe",
                "email": "jane@example.com",
                "full_name": "Jane Doe",
                "password": "SecurePass123",
            },
        )

    def test_login_success_returns_tokens(self, client):
        self._register(client)
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "janedoe", "password": "SecurePass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password_fails(self, client):
        self._register(client)
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "janedoe", "password": "WrongPassword"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user_fails(self, client):
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "ghost", "password": "SecurePass123"},
        )
        assert response.status_code == 401


class TestCurrentUser:
    def test_get_me_with_valid_token(self, client, registered_member):
        response = client.get("/api/v1/auth/me", headers=registered_member["headers"])
        assert response.status_code == 200
        assert response.json()["username"] == "member1"

    def test_get_me_without_token_fails(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_me_with_invalid_token_fails(self, client):
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401


class TestRoleBasedAuthorization:
    def test_member_cannot_add_book(self, client, registered_member):
        """MEMBER role should be forbidden from adding books (ADMIN/LIBRARIAN only)."""
        response = client.post(
            "/api/v1/books",
            json={
                "title": "Some Book",
                "author": "Some Author",
                "isbn": "1111111111",
                "category": "Fiction",
                "total_copies": 2,
            },
            headers=registered_member["headers"],
        )
        assert response.status_code == 403

    def test_admin_can_add_book(self, client, admin_user):
        response = client.post(
            "/api/v1/books",
            json={
                "title": "Some Book",
                "author": "Some Author",
                "isbn": "2222222222",
                "category": "Fiction",
                "total_copies": 2,
            },
            headers=admin_user["headers"],
        )
        assert response.status_code == 201
