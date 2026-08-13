import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, send_from_directory
from models.database import init_db
from services.exceptions import BusinessRuleError
from api.auth_routes import auth_bp
from api.wallet_routes import wallet_bp
from api.admin_routes import admin_bp

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

# ---- CORS (kept minimal, no external dependency needed) ----
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Idempotency-Key"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.route("/api/<path:_any>", methods=["OPTIONS"])
@app.route("/api", methods=["OPTIONS"], defaults={"_any": ""})
def cors_preflight(_any):
    return "", 200


# ---- Centralized error handling: API layer never contains business logic,
# but it IS responsible for translating service-layer errors into HTTP responses ----
@app.errorhandler(BusinessRuleError)
def handle_business_error(err):
    return jsonify({"success": False, "error": {"code": err.code, "message": err.message}}), err.status_code


@app.errorhandler(404)
def handle_404(err):
    return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": "Resource not found."}}), 404


@app.errorhandler(500)
def handle_500(err):
    return jsonify({"success": False, "error": {"code": "SERVER_ERROR", "message": "Internal server error."}}), 500


# ---- Blueprints (Controller layer) ----
app.register_blueprint(auth_bp)
app.register_blueprint(wallet_bp)
app.register_blueprint(admin_bp)


# ---- Serve the frontend ----
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
