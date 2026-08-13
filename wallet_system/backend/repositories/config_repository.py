from models.database import get_connection


class ConfigRepository:
    def get(self):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM wallet_configuration LIMIT 1").fetchone()
            return dict(row)
        finally:
            conn.close()

    def update(self, **kwargs):
        conn = get_connection()
        try:
            allowed = {
                "max_single_deposit", "max_single_withdrawal", "max_daily_withdrawal",
                "max_single_transfer", "max_daily_transfer",
            }
            fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
            if not fields:
                return self.get()
            set_sql = ", ".join(f"{k} = ?" for k in fields)
            conn.execute(f"UPDATE wallet_configuration SET {set_sql}", list(fields.values()))
            conn.commit()
            return self.get()
        finally:
            conn.close()
