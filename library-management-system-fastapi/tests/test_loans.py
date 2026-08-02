"""
Tests for loan management: issue, return, borrowing limits, fines, reports.
"""
from datetime import date, timedelta


def _create_book(client, headers, isbn="9780132350884", total_copies=1, **overrides):
    payload = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "isbn": isbn,
        "category": "Software Engineering",
        "total_copies": total_copies,
    }
    payload.update(overrides)
    return client.post("/api/v1/books", json=payload, headers=headers).json()


class TestIssueBook:
    def test_issue_book_success(self, client, admin_user, registered_member):
        book = _create_book(client, admin_user["headers"], total_copies=2)
        response = client.post(
            "/api/v1/loans/issue",
            json={"book_id": book["id"], "member_id": registered_member["id"]},
            headers=admin_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ISSUED"
        assert data["book_id"] == book["id"]

        # Verify available copies decremented
        book_after = client.get(f"/api/v1/books/{book['id']}", headers=admin_user["headers"]).json()
        assert book_after["available_copies"] == 1

    def test_issue_book_no_copies_available_fails(self, client, admin_user, registered_member):
        book = _create_book(client, admin_user["headers"], total_copies=1)
        client.post(
            "/api/v1/loans/issue",
            json={"book_id": book["id"], "member_id": registered_member["id"]},
            headers=admin_user["headers"],
        )
        # Second issue should fail - no copies left
        response = client.post(
            "/api/v1/loans/issue",
            json={"book_id": book["id"], "member_id": registered_member["id"]},
            headers=admin_user["headers"],
        )
        assert response.status_code == 422

    def test_issue_book_nonexistent_book_fails(self, client, admin_user, registered_member):
        response = client.post(
            "/api/v1/loans/issue",
            json={"book_id": 9999, "member_id": registered_member["id"]},
            headers=admin_user["headers"],
        )
        assert response.status_code == 404

    def test_member_cannot_exceed_max_active_loans(self, client, admin_user, registered_member):
        """MAX_ACTIVE_LOANS_PER_MEMBER default is 3."""
        for i in range(3):
            book = _create_book(client, admin_user["headers"], isbn=f"ISBN00000{i}", total_copies=1)
            resp = client.post(
                "/api/v1/loans/issue",
                json={"book_id": book["id"], "member_id": registered_member["id"]},
                headers=admin_user["headers"],
            )
            assert resp.status_code == 200

        # 4th loan should fail
        extra_book = _create_book(client, admin_user["headers"], isbn="ISBN_EXTRA", total_copies=1)
        response = client.post(
            "/api/v1/loans/issue",
            json={"book_id": extra_book["id"], "member_id": registered_member["id"]},
            headers=admin_user["headers"],
        )
        assert response.status_code == 422

    def test_member_cannot_issue_books(self, client, admin_user, registered_member):
        """Only ADMIN/LIBRARIAN can issue books, not MEMBER."""
        book = _create_book(client, admin_user["headers"])
        response = client.post(
            "/api/v1/loans/issue",
            json={"book_id": book["id"], "member_id": registered_member["id"]},
            headers=registered_member["headers"],
        )
        assert response.status_code == 403


class TestReturnBook:
    def test_return_book_on_time_no_fine(self, client, admin_user, registered_member):
        book = _create_book(client, admin_user["headers"], total_copies=1)
        client.post(
            "/api/v1/loans/issue",
            json={"book_id": book["id"], "member_id": registered_member["id"]},
            headers=admin_user["headers"],
        )
        response = client.post(
            "/api/v1/loans/return",
            json={"book_id": book["id"], "member_id": registered_member["id"]},
            headers=admin_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["fine_charged"] == 0
        assert data["loan"]["status"] == "RETURNED"

        # Verify available copies incremented back
        book_after = client.get(f"/api/v1/books/{book['id']}", headers=admin_user["headers"]).json()
        assert book_after["available_copies"] == 1

    def test_return_overdue_book_charges_fine(self, client, admin_user, registered_member, db_session):
        book = _create_book(client, admin_user["headers"], total_copies=1)
        client.post(
            "/api/v1/loans/issue",
            json={"book_id": book["id"], "member_id": registered_member["id"]},
            headers=admin_user["headers"],
        )

        # Simulate the loan being overdue by directly backdating due_date in the DB
        from app.models.loan import Loan

        loan = db_session.query(Loan).filter(Loan.book_id == book["id"]).first()
        loan.due_date = date.today() - timedelta(days=5)
        db_session.commit()

        response = client.post(
            "/api/v1/loans/return",
            json={"book_id": book["id"], "member_id": registered_member["id"]},
            headers=admin_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        # 5 days late * FINE_PER_DAY (default 10.0) = 50.0
        assert data["fine_charged"] == 50.0

    def test_return_without_active_loan_fails(self, client, admin_user, registered_member):
        book = _create_book(client, admin_user["headers"])
        response = client.post(
            "/api/v1/loans/return",
            json={"book_id": book["id"], "member_id": registered_member["id"]},
            headers=admin_user["headers"],
        )
        assert response.status_code == 404


class TestLoanReports:
    def test_my_history_returns_own_loans(self, client, admin_user, registered_member):
        book = _create_book(client, admin_user["headers"])
        client.post(
            "/api/v1/loans/issue",
            json={"book_id": book["id"], "member_id": registered_member["id"]},
            headers=admin_user["headers"],
        )
        response = client.get("/api/v1/loans/my-history", headers=registered_member["headers"])
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_overdue_report_admin_only(self, client, registered_member):
        response = client.get("/api/v1/loans/overdue", headers=registered_member["headers"])
        assert response.status_code == 403

    def test_overdue_report_lists_overdue_loans(self, client, admin_user, registered_member, db_session):
        book = _create_book(client, admin_user["headers"])
        client.post(
            "/api/v1/loans/issue",
            json={"book_id": book["id"], "member_id": registered_member["id"]},
            headers=admin_user["headers"],
        )
        from app.models.loan import Loan

        loan = db_session.query(Loan).filter(Loan.book_id == book["id"]).first()
        loan.due_date = date.today() - timedelta(days=1)
        db_session.commit()

        response = client.get("/api/v1/loans/overdue", headers=admin_user["headers"])
        assert response.status_code == 200
        assert len(response.json()) == 1
