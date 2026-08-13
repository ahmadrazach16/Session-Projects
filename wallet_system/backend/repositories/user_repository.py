"""
Repository / Data Access Layer for users.
Only raw queries here. No business rules.
"""
from models.database import get_connection


class UserRepository:

    def create(self, name, email, password_hash, role="CUSTOMER"):
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (name, email, password_hash, role),
            )
            conn.commit()
            return self.find_by_id(cur.lastrowid)
        finally:
            conn.close()

    def find_by_id(self, user_id):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def find_by_email(self, email):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_all(self, limit=50, offset=0):
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT id, name, email, role, status, created_at FROM users ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
