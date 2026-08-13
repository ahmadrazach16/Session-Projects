"""
Business / Service Layer for wallets.
All business decisions (limits, status checks, balance rules) live here.
The API layer must never contain logic like `if balance < amount: reject()`.
"""
import datetime
from models.database import get_connection
from repositories.wallet_repository import WalletRepository
from repositories.transaction_repository import TransactionRepository
from repositories.config_repository import ConfigRepository
from services.exceptions import BusinessRuleError, NotFoundError, ForbiddenError

SUPPORTED_CURRENCIES = {"USD", "PKR", "EUR", "GBP"}


class WalletService:
    def __init__(self):
        self.wallet_repo = WalletRepository()
        self.tx_repo = TransactionRepository()
        self.config_repo = ConfigRepository()

    # ---------- Wallet creation / viewing ----------

    def create_wallet(self, user_id, currency):
        currency = (currency or "").upper().strip()
        if currency not in SUPPORTED_CURRENCIES:
            raise BusinessRuleError(f"Unsupported currency '{currency}'.")

        existing = self.wallet_repo.find_by_user_and_currency(user_id, currency)
        if existing:
            raise BusinessRuleError(
                f"You already have an active {currency} wallet. Only one wallet per currency is allowed.",
                code="WALLET_EXISTS",
            )
        return self.wallet_repo.create(user_id, currency)

    def get_wallet(self, wallet_id, requesting_user_id, is_admin=False):
        wallet = self.wallet_repo.find_by_id(wallet_id)
        if not wallet:
            raise NotFoundError("Wallet not found.")
        if not is_admin and wallet["user_id"] != requesting_user_id:
            raise ForbiddenError("You do not have access to this wallet.")
        return wallet

    def list_my_wallets(self, user_id):
        return self.wallet_repo.list_by_user(user_id)

    # ---------- Shared validation helpers ----------

    def _validate_wallet_active(self, wallet):
        if wallet["status"] == "FROZEN":
            raise BusinessRuleError("This wallet is frozen and cannot perform transactions.", code="WALLET_FROZEN")
        if wallet["status"] == "CLOSED":
            raise BusinessRuleError("This wallet is closed and cannot perform transactions.", code="WALLET_CLOSED")

    def _validate_amount(self, amount):
        if amount is None:
            raise BusinessRuleError("Amount is required.")
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise BusinessRuleError("Amount must be a number.")
        if amount <= 0:
            raise BusinessRuleError("Amount must be greater than zero.")
        return amount

    def _since_start_of_day_iso(self):
        return datetime.datetime.utcnow().strftime("%Y-%m-%d 00:00:00")

    # ---------- Deposit ----------

    def deposit(self, wallet_id, user_id, amount, description=None, idempotency_key=None):
        # Idempotency check
        existing_tx = self.tx_repo.find_by_idempotency_key(idempotency_key)
        if existing_tx:
            return existing_tx

        amount = self._validate_amount(amount)

        wallet = self.wallet_repo.find_by_id(wallet_id)
        if not wallet:
            raise NotFoundError("Wallet not found.")
        if wallet["user_id"] != user_id:
            raise ForbiddenError("This wallet does not belong to you.")
        self._validate_wallet_active(wallet)

        config = self.config_repo.get()
        if amount > config["max_single_deposit"]:
            raise BusinessRuleError(
                f"Amount exceeds the maximum single deposit limit of {config['max_single_deposit']}.",
                code="LIMIT_EXCEEDED",
            )

        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            fresh_wallet = self.wallet_repo.find_by_id_for_update(wallet_id, conn)
            new_balance = fresh_wallet["balance"] + amount
            self.wallet_repo.update_balance(wallet_id, new_balance, conn)
            tx = self.tx_repo.create(
                conn,
                idempotency_key=idempotency_key,
                type="DEPOSIT",
                status="COMPLETED",
                amount=amount,
                currency=wallet["currency"],
                source_wallet_id=None,
                destination_wallet_id=wallet_id,
                description=description or "Wallet deposit",
            )
            conn.commit()
            return tx
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------- Withdrawal ----------

    def withdraw(self, wallet_id, user_id, amount, description=None, idempotency_key=None):
        existing_tx = self.tx_repo.find_by_idempotency_key(idempotency_key)
        if existing_tx:
            return existing_tx

        amount = self._validate_amount(amount)

        wallet = self.wallet_repo.find_by_id(wallet_id)
        if not wallet:
            raise NotFoundError("Wallet not found.")
        if wallet["user_id"] != user_id:
            raise ForbiddenError("This wallet does not belong to you.")
        self._validate_wallet_active(wallet)

        config = self.config_repo.get()
        if amount > config["max_single_withdrawal"]:
            raise BusinessRuleError(
                f"Amount exceeds the maximum single withdrawal limit of {config['max_single_withdrawal']}.",
                code="LIMIT_EXCEEDED",
            )

        already_withdrawn_today = self.wallet_repo.sum_amount_since(
            wallet_id, "WITHDRAWAL", self._since_start_of_day_iso()
        )
        if already_withdrawn_today + amount > config["max_daily_withdrawal"]:
            raise BusinessRuleError(
                f"This withdrawal would exceed your daily withdrawal limit of {config['max_daily_withdrawal']}.",
                code="DAILY_LIMIT_EXCEEDED",
            )

        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            fresh_wallet = self.wallet_repo.find_by_id_for_update(wallet_id, conn)

            if fresh_wallet["balance"] < amount:
                tx = self.tx_repo.create(
                    conn,
                    idempotency_key=idempotency_key,
                    type="WITHDRAWAL",
                    status="FAILED",
                    amount=amount,
                    currency=wallet["currency"],
                    source_wallet_id=wallet_id,
                    destination_wallet_id=None,
                    description=description or "Wallet withdrawal",
                    failure_reason="Insufficient balance",
                )
                conn.commit()
                raise BusinessRuleError("Insufficient balance for this withdrawal.", code="INSUFFICIENT_BALANCE")

            new_balance = fresh_wallet["balance"] - amount
            self.wallet_repo.update_balance(wallet_id, new_balance, conn)
            tx = self.tx_repo.create(
                conn,
                idempotency_key=idempotency_key,
                type="WITHDRAWAL",
                status="COMPLETED",
                amount=amount,
                currency=wallet["currency"],
                source_wallet_id=wallet_id,
                destination_wallet_id=None,
                description=description or "Wallet withdrawal",
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
