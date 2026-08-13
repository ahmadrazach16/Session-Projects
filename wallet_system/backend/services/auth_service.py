import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from repositories.user_repository import UserRepository
from services.exceptions import BusinessRuleError, UnauthorizedError

JWT_SECRET = "wallet-system-super-secret-key-change-in-production"
JWT_ALGO = "HS256"
JWT_EXPIRY_HOURS = 12


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    def register(self, name, email, password):
        if not name or not name.strip():
            raise BusinessRuleError("Name is required.")
        if not email or "@" not in email:
            raise BusinessRuleError("A valid email is required.")
        if not password or len(password) < 6:
            raise BusinessRuleError("Password must be at least 6 characters.")

        existing = self.user_repo.find_by_email(email.lower().strip())
        if existing:
            raise BusinessRuleError("An account with this email already exists.", code="EMAIL_TAKEN")

        password_hash = generate_password_hash(password)
        user = self.user_repo.create(name.strip(), email.lower().strip(), password_hash, role="CUSTOMER")
        return self._sanitize(user)

    def login(self, email, password):
        user = self.user_repo.find_by_email((email or "").lower().strip())
        if not user or not check_password_hash(user["password_hash"], password or ""):
            raise UnauthorizedError("Invalid email or password.")
        if user["status"] != "ACTIVE":
            raise UnauthorizedError("This account has been disabled.")

        token = self._generate_token(user)
        return {"token": token, "user": self._sanitize(user)}

    def _generate_token(self, user):
        payload = {
            "user_id": user["id"],
            "role": user["role"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

    def verify_token(self, token):
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("Session expired. Please log in again.")
        except jwt.InvalidTokenError:
            raise UnauthorizedError("Invalid authentication token.")

        user = self.user_repo.find_by_id(payload["user_id"])
        if not user or user["status"] != "ACTIVE":
            raise UnauthorizedError("Account not found or disabled.")
        return self._sanitize(user)

    def _sanitize(self, user):
        return {k: v for k, v in user.items() if k != "password_hash"}
