"""
Tests for book management: add, update, delete, search.
"""


def _create_book(client, headers, isbn="9780132350884", **overrides):
    payload = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "isbn": isbn,
        "category": "Software Engineering",
        "total_copies": 3,
    }
    payload.update(overrides)
    return client.post("/api/v1/books", json=payload, headers=headers)


class TestAddBook:
    def test_add_book_success(self, client, admin_user):
        response = _create_book(client, admin_user["headers"])
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Clean Code"
        assert data["available_copies"] == 3
        assert data["total_copies"] == 3

    def test_add_book_duplicate_isbn_fails(self, client, admin_user):
        _create_book(client, admin_user["headers"], isbn="1234567890")
        response = _create_book(client, admin_user["headers"], isbn="1234567890")
        assert response.status_code == 409

    def test_add_book_unauthenticated_fails(self, client):
        response = _create_book(client, headers={})
        assert response.status_code == 401


class TestSearchBooks:
    def test_search_by_title(self, client, admin_user, registered_member):
        _create_book(client, admin_user["headers"], isbn="1111111111", title="Design Patterns")
        _create_book(client, admin_user["headers"], isbn="2222222222", title="Clean Architecture")

        response = client.get(
            "/api/v1/books", params={"title": "Design"}, headers=registered_member["headers"]
        )
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["title"] == "Design Patterns"

    def test_search_no_filters_returns_all(self, client, admin_user, registered_member):
        _create_book(client, admin_user["headers"], isbn="1111111111")
        _create_book(client, admin_user["headers"], isbn="2222222222", title="Another Book")

        response = client.get("/api/v1/books", headers=registered_member["headers"])
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestGetBook:
    def test_get_existing_book(self, client, admin_user, registered_member):
        created = _create_book(client, admin_user["headers"]).json()
        response = client.get(f"/api/v1/books/{created['id']}", headers=registered_member["headers"])
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_nonexistent_book_returns_404(self, client, registered_member):
        response = client.get("/api/v1/books/9999", headers=registered_member["headers"])
        assert response.status_code == 404


class TestUpdateBook:
    def test_update_book_title(self, client, admin_user):
        created = _create_book(client, admin_user["headers"]).json()
        response = client.put(
            f"/api/v1/books/{created['id']}",
            json={"title": "Clean Code (2nd Edition)"},
            headers=admin_user["headers"],
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Clean Code (2nd Edition)"

    def test_member_cannot_update_book(self, client, admin_user, registered_member):
        created = _create_book(client, admin_user["headers"]).json()
        response = client.put(
            f"/api/v1/books/{created['id']}",
            json={"title": "Hacked Title"},
            headers=registered_member["headers"],
        )
        assert response.status_code == 403


class TestDeleteBook:
    def test_delete_book_success(self, client, admin_user):
        created = _create_book(client, admin_user["headers"]).json()
        response = client.delete(f"/api/v1/books/{created['id']}", headers=admin_user["headers"])
        assert response.status_code == 204

        get_response = client.get(f"/api/v1/books/{created['id']}", headers=admin_user["headers"])
        assert get_response.status_code == 404

    def test_delete_nonexistent_book_returns_404(self, client, admin_user):
        response = client.delete("/api/v1/books/9999", headers=admin_user["headers"])
        assert response.status_code == 404
