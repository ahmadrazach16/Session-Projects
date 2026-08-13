"""
Repository / Data Access Layer for wallets.
Only raw queries here. No business rules.
"""
from models.database import get_connection


class WalletRepository:

    def create(self, user_id, currency, conn=None):
        owns_conn = conn is None
        conn = conn or get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO wallets (user_id, currency, balance, status) VALUES (?, ?, 0, 'ACTIVE')",
                (user_id, currency),
            )
            if owns_conn:
                conn.commit()
            return self.find_by_id(cur.lastrowid, conn=conn)
        finally:
            if owns_conn:
                conn.close()

    def find_by_id(self, wallet_id, conn=None):
        owns_conn = conn is None
        conn = conn or get_connection()
        try:
            row = conn.execute("SELECT * FROM wallets WHERE id = ?", (wallet_id,)).fetchone()
            return dict(row) if row else None
        finally:
            if owns_conn:
                conn.close()

    def find_by_id_for_update(self, wallet_id, conn):
        """Must be called inside an open transaction (conn) to lock the row."""
        row = conn.execute("SELECT * FROM wallets WHERE id = ?", (wallet_id,)).fetchone()
        return dict(row) if row else None

    def find_by_user_and_currency(self, user_id, currency):
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM wallets WHERE user_id = ? AND currency = ?", (user_id, currency)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_by_user(self, user_id):
        conn = get_connection()
        try:
            rows = conn.execute("SELECT * FROM wallets WHERE user_id = ?", (user_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def list_all(self, limit=50, offset=0):
        conn = get_connection()
        try:
            rows = conn.execute(
                """SELECT w.*, u.name as owner_name, u.email as owner_email
                   FROM wallets w JOIN users u ON u.id = w.user_id
                   ORDER BY w.id DESC LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_balance(self, wallet_id, new_balance, conn):
        """Must be called inside an open transaction (conn)."""
        conn.execute(
            "UPDATE wallets SET balance = ?, updated_at = datetime('now') WHERE id = ?",
            (new_balance, wallet_id),
        )

    def update_status(self, wallet_id, status):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE wallets SET status = ?, updated_at = datetime('now') WHERE id = ?",
                (status, wallet_id),
            )
            conn.commit()
            return self.find_by_id(wallet_id)
        finally:
            conn.close()

    def sum_amount_since(self, wallet_id, tx_type, since_iso, conn=None, as_source=True):
        """Sum of COMPLETED transactions of a given type for daily-limit checks."""
        owns_conn = conn is None
        conn = conn or get_connection()
        try:
            col = "source_wallet_id" if as_source else "destination_wallet_id"
            row = conn.execute(
                f"""SELECT COALESCE(SUM(amount), 0) as total FROM transactions
                    WHERE {col} = ? AND type = ? AND status = 'COMPLETED'
                    AND created_at >= ?""",
                (wallet_id, tx_type, since_iso),
            ).fetchone()
            return row["total"]
        finally:
            if owns_conn:
                conn.close()
