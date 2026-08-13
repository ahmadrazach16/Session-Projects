from repositories.transaction_repository import TransactionRepository
from repositories.wallet_repository import WalletRepository
from services.exceptions import NotFoundError, ForbiddenError


class TransactionService:
    def __init__(self):
        self.tx_repo = TransactionRepository()
        self.wallet_repo = WalletRepository()

    def list_transactions(self, user_id, filters, page=1, page_size=20):
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 20)))
        offset = (page - 1) * page_size

        my_wallets = self.wallet_repo.list_by_user(user_id)
        wallet_ids = [w["id"] for w in my_wallets]

        items, total = self.tx_repo.search(wallet_ids, filters, limit=page_size, offset=offset)
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if page_size else 0,
        }

    def get_transaction_detail(self, tx_id, user_id, is_admin=False):
        tx = self.tx_repo.find_by_id(tx_id)
        if not tx:
            raise NotFoundError("Transaction not found.")

        if not is_admin:
            my_wallets = {w["id"] for w in self.wallet_repo.list_by_user(user_id)}
            if tx["source_wallet_id"] not in my_wallets and tx["destination_wallet_id"] not in my_wallets:
                raise ForbiddenError("You do not have access to this transaction.")
        return tx

    def list_all_transactions_admin(self, filters, page=1, page_size=20):
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 20)))
        offset = (page - 1) * page_size
        items, total = self.tx_repo.search(None, filters, limit=page_size, offset=offset)
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if page_size else 0,
        }
