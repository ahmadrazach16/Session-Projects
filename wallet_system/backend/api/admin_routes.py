from flask import Blueprint, request, jsonify, g
from services.admin_wallet_service import AdminWalletService
from services.transaction_service import TransactionService
from repositories.config_repository import ConfigRepository
from api.auth_middleware import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

admin_service = AdminWalletService()
transaction_service = TransactionService()
config_repo = ConfigRepository()


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    users = admin_service.list_users(
        page=request.args.get("page", 1, type=int),
        page_size=request.args.get("page_size", 50, type=int),
    )
    return jsonify({"success": True, "data": users}), 200


@admin_bp.route("/wallets", methods=["GET"])
@admin_required
def list_wallets():
    wallets = admin_service.list_wallets(
        page=request.args.get("page", 1, type=int),
        page_size=request.args.get("page_size", 50, type=int),
    )
    return jsonify({"success": True, "data": wallets}), 200


@admin_bp.route("/wallets/<int:wallet_id>/freeze", methods=["POST"])
@admin_required
def freeze_wallet(wallet_id):
    wallet = admin_service.freeze_wallet(wallet_id)
    return jsonify({"success": True, "data": wallet}), 200


@admin_bp.route("/wallets/<int:wallet_id>/unfreeze", methods=["POST"])
@admin_required
def unfreeze_wallet(wallet_id):
    wallet = admin_service.unfreeze_wallet(wallet_id)
    return jsonify({"success": True, "data": wallet}), 200


@admin_bp.route("/wallets/<int:wallet_id>/adjust-balance", methods=["POST"])
@admin_required
def adjust_balance(wallet_id):
    data = request.get_json(force=True, silent=True) or {}
    tx = admin_service.adjust_balance(
        wallet_id=wallet_id,
        amount=data.get("amount"),
        reason=data.get("reason"),
        admin_id=g.current_user["id"],
    )
    return jsonify({"success": True, "data": tx}), 201


@admin_bp.route("/transactions", methods=["GET"])
@admin_required
def list_all_transactions():
    filters = {
        "type": request.args.get("type"),
        "status": request.args.get("status"),
        "date_from": request.args.get("date_from"),
        "date_to": request.args.get("date_to"),
        "amount_min": request.args.get("amount_min", type=float),
        "amount_max": request.args.get("amount_max", type=float),
        "reference": request.args.get("reference"),
    }
    result = transaction_service.list_all_transactions_admin(
        filters,
        page=request.args.get("page", 1, type=int),
        page_size=request.args.get("page_size", 20, type=int),
    )
    return jsonify({"success": True, "data": result}), 200


@admin_bp.route("/transactions/failed", methods=["GET"])
@admin_required
def investigate_failed():
    result = admin_service.investigate_failed_transactions(
        page=request.args.get("page", 1, type=int),
        page_size=request.args.get("page_size", 50, type=int),
    )
    return jsonify({"success": True, "data": result}), 200


@admin_bp.route("/config", methods=["GET"])
@admin_required
def get_config():
    return jsonify({"success": True, "data": config_repo.get()}), 200


@admin_bp.route("/config", methods=["PUT"])
@admin_required
def update_config():
    data = request.get_json(force=True, silent=True) or {}
    config = config_repo.update(**data)
    return jsonify({"success": True, "data": config}), 200
