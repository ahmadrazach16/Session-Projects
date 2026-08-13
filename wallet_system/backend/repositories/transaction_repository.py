"""
Repository / Data Access Layer for transactions.
Only raw queries here. No business rules.
"""
import random
from datetime import datetime
from models.database import get_connection


class TransactionRepository:

    def generate_reference(self):
        """
        Application-side reference generation.
        Format: TXN-YYYYMMDD-XXXXXX (random suffix + DB UNIQUE constraint
        guarantees uniqueness even under concurrent requests - if a clash
        ever happens the UNIQUE constraint raises IntegrityError and the
        caller retries).
        """
        date_part = datetime.utcnow().strftime("%Y%m%d")
        rand_part = f"{random.randint(0, 999999):06d}"
        return f"TXN-{date_part}-{rand_part}"

    def find_by_idempotency_key(self, idempotency_key, conn=None):
        if not idempotency_key:
            return None
        owns_conn = conn is None
        conn = conn or get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM transactions WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            if owns_conn:
                conn.close()

    def create(self, conn, **kwargs):
        """Must be called inside an open transaction (conn)."""
        for attempt in range(5):
            reference = kwargs.get("reference") or self.generate_reference()
            try:
                cur = conn.execute(
                    """INSERT INTO transactions
                       (reference, idempotency_key, type, status, amount, currency,
                        source_wallet_id, destination_wallet_id, description, failure_reason)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        reference,
                        kwargs.get("idempotency_key"),
                        kwargs["type"],
                        kwargs["status"],
                        kwargs["amount"],
                        kwargs["currency"],
                        kwargs.get("source_wallet_id"),
                        kwargs.get("destination_wallet_id"),
                        kwargs.get("description"),
                        kwargs.get("failure_reason"),
                    ),
                )
                return self.find_by_id(cur.lastrowid, conn=conn)
            except Exception as e:
                if "UNIQUE" in str(e) and "reference" in str(e) and attempt < 4:
                    kwargs.pop("reference", None)
                    continue
                raise

    def update_status(self, tx_id, status, conn, failure_reason=None):
        conn.execute(
            "UPDATE transactions SET status = ?, failure_reason = ?, updated_at = datetime('now') WHERE id = ?",
            (status, failure_reason, tx_id),
        )

    def find_by_id(self, tx_id, conn=None):
        owns_conn = conn is None
        conn = conn or get_connection()
        try:
            row = conn.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,)).fetchone()
            return dict(row) if row else None
        finally:
            if owns_conn:
                conn.close()

    def find_by_reference(self, reference):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM transactions WHERE reference = ?", (reference,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def search(self, wallet_ids, filters, limit=20, offset=0):
        """
        wallet_ids: list of wallet ids the requesting user owns (for scoping),
                    or None for admin (no scoping).
        filters: dict with optional keys: type, status, date_from, date_to,
                 amount_min, amount_max, reference
        """
        conn = get_connection()
        try:
            clauses = []
            params = []

            if wallet_ids is not None:
                if not wallet_ids:
                    return [], 0
                placeholders = ",".join("?" * len(wallet_ids))
                clauses.append(
                    f"(source_wallet_id IN ({placeholders}) OR destination_wallet_id IN ({placeholders}))"
                )
                params.extend(wallet_ids)
                params.extend(wallet_ids)

            if filters.get("type"):
                clauses.append("type = ?")
                params.append(filters["type"])
            if filters.get("status"):
                clauses.append("status = ?")
                params.append(filters["status"])
            if filters.get("date_from"):
                clauses.append("created_at >= ?")
                params.append(filters["date_from"])
            if filters.get("date_to"):
                clauses.append("created_at <= ?")
                params.append(filters["date_to"])
            if filters.get("amount_min") is not None:
                clauses.append("amount >= ?")
                params.append(filters["amount_min"])
            if filters.get("amount_max") is not None:
                clauses.append("amount <= ?")
                params.append(filters["amount_max"])
            if filters.get("reference"):
                clauses.append("reference LIKE ?")
                params.append(f"%{filters['reference']}%")

            where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""

            count_row = conn.execute(
                f"SELECT COUNT(*) as c FROM transactions {where_sql}", params
            ).fetchone()
            total = count_row["c"]

            rows = conn.execute(
                f"""SELECT * FROM transactions {where_sql}
                    ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?""",
                params + [limit, offset],
            ).fetchall()

            return [dict(r) for r in rows], total
        finally:
            conn.close()
