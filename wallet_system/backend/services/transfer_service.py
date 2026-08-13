"""
Business / Service Layer for money transfers.
This is the most important part of the system: it must be atomic,
idempotent, and enforce every transfer business rule before touching
the database.
"""
import datetime
from models.database import get_connection
from repositories.wallet_repository import WalletRepository
from repositories.transaction_repository import TransactionRepository
from repositories.config_repository import ConfigRepository
from services.exceptions import BusinessRuleError, NotFoundError, ForbiddenError


class TransferService:
    def __init__(self):
        self.wallet_repo = WalletRepository()
        self.tx_repo = TransactionRepository()
        self.config_repo = ConfigRepository()

    def _since_start_of_day_iso(self):
        return datetime.datetime.utcnow().strftime("%Y-%m-%d 00:00:00")

    def transfer(self, sender_wallet_id, receiver_wallet_id, amount, user_id,
                 description=None, idempotency_key=None):

        # ---- Idempotency: if this exact request was already processed, return it ----
        existing_tx = self.tx_repo.find_by_idempotency_key(idempotency_key)
        if existing_tx:
            return existing_tx

        # ---- Rule 5: amount must be positive ----
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise BusinessRuleError("Amount must be a number.")
        if amount <= 0:
            raise BusinessRuleError("Amount must be greater than zero.")

        # ---- Rule 1 & 2: both wallets must exist ----
        sender = self.wallet_repo.find_by_id(sender_wallet_id)
        if not sender:
            raise NotFoundError("Sender wallet not found.")
        if sender["user_id"] != user_id:
            raise ForbiddenError("Sender wallet does not belong to you.")

        receiver = self.wallet_repo.find_by_id(receiver_wallet_id)
        if not receiver:
            raise NotFoundError("Receiver wallet not found.")

        # ---- Rule 3: cannot transfer to self ----
        if sender["id"] == receiver["id"]:
            raise BusinessRuleError("You cannot transfer money to your own wallet.", code="SELF_TRANSFER")

        # ---- Rule 4: both wallets must be active ----
        if sender["status"] != "ACTIVE":
            raise BusinessRuleError("Your wallet is not active (frozen/closed).", code="WALLET_NOT_ACTIVE")
        if receiver["status"] != "ACTIVE":
            raise BusinessRuleError("Receiver wallet is not active (frozen/closed).", code="WALLET_NOT_ACTIVE")

        if sender["currency"] != receiver["currency"]:
            raise BusinessRuleError("Cross-currency transfers are not supported.", code="CURRENCY_MISMATCH")

        # ---- Rule 7: single + daily transfer limit ----
        config = self.config_repo.get()
        if amount > config["max_single_transfer"]:
            raise BusinessRuleError(
                f"Amount exceeds the maximum single transfer limit of {config['max_single_transfer']}.",
                code="LIMIT_EXCEEDED",
            )
        already_transferred_today = self.wallet_repo.sum_amount_since(
            sender["id"], "TRANSFER", self._since_start_of_day_iso()
        )
        if already_transferred_today + amount > config["max_daily_transfer"]:
            raise BusinessRuleError(
                f"This transfer would exceed your daily transfer limit of {config['max_daily_transfer']}.",
                code="DAILY_LIMIT_EXCEEDED",
            )

        # ---- Rule 8: atomic transaction ----
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")

            fresh_sender = self.wallet_repo.find_by_id_for_update(sender["id"], conn)
            fresh_receiver = self.wallet_repo.find_by_id_for_update(receiver["id"], conn)

            # Re-check status/balance inside the transaction to avoid race conditions
            if fresh_sender["status"] != "ACTIVE" or fresh_receiver["status"] != "ACTIVE":
                tx = self.tx_repo.create(
                    conn, idempotency_key=idempotency_key, type="TRANSFER", status="FAILED",
                    amount=amount, currency=sender["currency"],
                    source_wallet_id=sender["id"], destination_wallet_id=receiver["id"],
                    description=description, failure_reason="Wallet not active",
                )
                conn.commit()
                raise BusinessRuleError("Wallet is not active.", code="WALLET_NOT_ACTIVE")

            # ---- Rule 6: sufficient balance ----
            if fresh_sender["balance"] < amount:
                tx = self.tx_repo.create(
                    conn, idempotency_key=idempotency_key, type="TRANSFER", status="FAILED",
                    amount=amount, currency=sender["currency"],
                    source_wallet_id=sender["id"], destination_wallet_id=receiver["id"],
                    description=description, failure_reason="Insufficient balance",
                )
                conn.commit()
                raise BusinessRuleError("Insufficient balance for this transfer.", code="INSUFFICIENT_BALANCE")

            # Debit sender, credit receiver - all inside one DB transaction.
            self.wallet_repo.update_balance(sender["id"], fresh_sender["balance"] - amount, conn)
            self.wallet_repo.update_balance(receiver["id"], fresh_receiver["balance"] + amount, conn)

            tx = self.tx_repo.create(
                conn,
                idempotency_key=idempotency_key,
                type="TRANSFER",
                status="COMPLETED",
                amount=amount,
                currency=sender["currency"],
                source_wallet_id=sender["id"],
                destination_wallet_id=receiver["id"],
                description=description or "Wallet transfer",
            )
            conn.commit()  # Either everything above succeeds, or...
            return tx
        except BusinessRuleError:
            raise
        except Exception:
            conn.rollback()  # ...nothing is applied. No partial updates possible.
            raise
        finally:
            conn.close()
