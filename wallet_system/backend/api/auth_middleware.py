from functools import wraps
from flask import request, g, jsonify
from services.auth_service import AuthService
from services.exceptions import UnauthorizedError, ForbiddenError

auth_service = AuthService()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise UnauthorizedError("Missing or invalid Authorization header.")
        token = auth_header.split(" ", 1)[1]
        g.current_user = auth_service.verify_token(token)
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise UnauthorizedError("Missing or invalid Authorization header.")
        token = auth_header.split(" ", 1)[1]
        user = auth_service.verify_token(token)
        if user["role"] != "ADMIN":
            raise ForbiddenError("Admin access required.")
        g.current_user = user
        return f(*args, **kwargs)
    return wrapper
