from flask import Blueprint, request, jsonify, g
from services.wallet_service import WalletService
from services.transfer_service import TransferService
from services.transaction_service import TransactionService
from api.auth_middleware import login_required

wallet_bp = Blueprint("wallet", __name__, url_prefix="/api/wallet")

wallet_service = WalletService()
transfer_service = TransferService()
transaction_service = TransactionService()


@wallet_bp.route("", methods=["POST"])
@login_required
def create_wallet():
    data = request.get_json(force=True, silent=True) or {}
    wallet = wallet_service.create_wallet(g.current_user["id"], data.get("currency"))
    return jsonify({"success": True, "data": wallet}), 201


@wallet_bp.route("", methods=["GET"])
@login_required
def list_my_wallets():
    wallets = wallet_service.list_my_wallets(g.current_user["id"])
    return jsonify({"success": True, "data": wallets}), 200


@wallet_bp.route("/<int:wallet_id>", methods=["GET"])
@login_required
def get_wallet(wallet_id):
    wallet = wallet_service.get_wallet(wallet_id, g.current_user["id"])
    return jsonify({"success": True, "data": wallet}), 200


@wallet_bp.route("/deposit", methods=["POST"])
@login_required
def deposit():
    data = request.get_json(force=True, silent=True) or {}
    idempotency_key = request.headers.get("Idempotency-Key")
    tx = wallet_service.deposit(
        wallet_id=data.get("wallet_id"),
        user_id=g.current_user["id"],
        amount=data.get("amount"),
        description=data.get("description"),
        idempotency_key=idempotency_key,
    )
    return jsonify({"success": True, "data": tx}), 201


@wallet_bp.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    data = request.get_json(force=True, silent=True) or {}
    idempotency_key = request.headers.get("Idempotency-Key")
    tx = wallet_service.withdraw(
        wallet_id=data.get("wallet_id"),
        user_id=g.current_user["id"],
        amount=data.get("amount"),
        description=data.get("description"),
        idempotency_key=idempotency_key,
    )
    return jsonify({"success": True, "data": tx}), 201


@wallet_bp.route("/transfer", methods=["POST"])
@login_required
def transfer():
    data = request.get_json(force=True, silent=True) or {}
    idempotency_key = request.headers.get("Idempotency-Key")
    tx = transfer_service.transfer(
        sender_wallet_id=data.get("sender_wallet_id"),
        receiver_wallet_id=data.get("recipient_wallet_id"),
        amount=data.get("amount"),
        user_id=g.current_user["id"],
        description=data.get("description"),
        idempotency_key=idempotency_key,
    )
    return jsonify({"success": True, "data": tx}), 201


@wallet_bp.route("/transactions", methods=["GET"])
@login_required
def list_transactions():
    filters = {
        "type": request.args.get("type"),
        "status": request.args.get("status"),
        "date_from": request.args.get("date_from"),
        "date_to": request.args.get("date_to"),
        "amount_min": request.args.get("amount_min", type=float),
        "amount_max": request.args.get("amount_max", type=float),
        "reference": request.args.get("reference"),
    }
    result = transaction_service.list_transactions(
        g.current_user["id"], filters,
        page=request.args.get("page", 1, type=int),
        page_size=request.args.get("page_size", 20, type=int),
    )
    return jsonify({"success": True, "data": result}), 200


@wallet_bp.route("/transactions/<int:tx_id>", methods=["GET"])
@login_required
def get_transaction(tx_id):
    is_admin = g.current_user["role"] == "ADMIN"
    tx = transaction_service.get_transaction_detail(tx_id, g.current_user["id"], is_admin=is_admin)
    return jsonify({"success": True, "data": tx}), 200
