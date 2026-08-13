from flask import Blueprint, request, jsonify, g
from services.auth_service import AuthService
from api.auth_middleware import login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
auth_service = AuthService()


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True, silent=True) or {}
    user = auth_service.register(data.get("name"), data.get("email"), data.get("password"))
    return jsonify({"success": True, "data": user}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    result = auth_service.login(data.get("email"), data.get("password"))
    return jsonify({"success": True, "data": result}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    return jsonify({"success": True, "data": g.current_user}), 200
