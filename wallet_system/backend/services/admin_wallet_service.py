from models.database import get_connection
from repositories.user_repository import UserRepository
from repositories.wallet_repository import WalletRepository
from repositories.transaction_repository import TransactionRepository
from services.exceptions import BusinessRuleError, NotFoundError


class AdminWalletService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.wallet_repo = WalletRepository()
        self.tx_repo = TransactionRepository()

    def list_users(self, page=1, page_size=50):
        offset = (max(1, page) - 1) * page_size
        return self.user_repo.list_all(limit=page_size, offset=offset)

    def list_wallets(self, page=1, page_size=50):
        offset = (max(1, page) - 1) * page_size
        return self.wallet_repo.list_all(limit=page_size, offset=offset)

    def freeze_wallet(self, wallet_id):
        wallet = self.wallet_repo.find_by_id(wallet_id)
        if not wallet:
            raise NotFoundError("Wallet not found.")
        if wallet["status"] == "FROZEN":
            raise BusinessRuleError("Wallet is already frozen.")
        if wallet["status"] == "CLOSED":
            raise BusinessRuleError("Cannot freeze a closed wallet.")
        return self.wallet_repo.update_status(wallet_id, "FROZEN")

    def unfreeze_wallet(self, wallet_id):
        wallet = self.wallet_repo.find_by_id(wallet_id)
        if not wallet:
            raise NotFoundError("Wallet not found.")
        if wallet["status"] != "FROZEN":
            raise BusinessRuleError("Wallet is not currently frozen.")
        return self.wallet_repo.update_status(wallet_id, "ACTIVE")

    def adjust_balance(self, wallet_id, amount, reason, admin_id):
        """
        Controlled balance correction. Never a raw PUT of balance -
        always goes through this auditable, transactional operation and
        always produces a transaction record explaining the change.
        """
        if not reason or not reason.strip():
            raise BusinessRuleError("A reason is required for balance adjustments.")
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise BusinessRuleError("Amount must be a number.")
        if amount == 0:
            raise BusinessRuleError("Adjustment amount cannot be zero.")

        wallet = self.wallet_repo.find_by_id(wallet_id)
        if not wallet:
            raise NotFoundError("Wallet not found.")

        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            fresh = self.wallet_repo.find_by_id_for_update(wallet_id, conn)

            new_balance = fresh["balance"] + amount
            if new_balance < 0:
                tx = self.tx_repo.create(
                    conn, type="ADJUSTMENT", status="FAILED", amount=abs(amount),
                    currency=wallet["currency"], source_wallet_id=wallet_id if amount < 0 else None,
                    destination_wallet_id=wallet_id if amount > 0 else None,
                    description=f"[Admin #{admin_id}] {reason}",
                    failure_reason="Adjustment would make balance negative",
                )
                conn.commit()
                raise BusinessRuleError("This adjustment would make the balance negative.")

            self.wallet_repo.update_balance(wallet_id, new_balance, conn)
            tx = self.tx_repo.create(
                conn, type="ADJUSTMENT", status="COMPLETED", amount=abs(amount),
                currency=wallet["currency"],
                source_wallet_id=wallet_id if amount < 0 else None,
                destination_wallet_id=wallet_id if amount > 0 else None,
                description=f"[Admin #{admin_id}] {reason}",
            )
            conn.commit()
            return tx
        except BusinessRuleError:
            raise
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def investigate_failed_transactions(self, page=1, page_size=50):
        offset = (max(1, page) - 1) * page_size
        items, total = self.tx_repo.search(None, {"status": "FAILED"}, limit=page_size, offset=offset)
        return {"items": items, "total": total, "page": page, "page_size": page_size}
