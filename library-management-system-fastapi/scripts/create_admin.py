"""
Bootstrap script to create (or promote) an ADMIN user.

Self-registration via /api/v1/auth/register always creates a MEMBER
(by design, to prevent privilege escalation through the public API).
Use this script once, after deployment, to create your first admin:

    python scripts/create_admin.py --username admin --email admin@library.com --password ChangeMe123

If the username already exists, it will be promoted to ADMIN instead.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import PasswordHasher  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


def create_or_promote_admin(username: str, email: str, full_name: str, password: str) -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            existing.role = UserRole.ADMIN
            db.commit()
            print(f"✅ Existing user '{username}' promoted to ADMIN.")
            return

        admin = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=PasswordHasher.hash(password),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        print(f"✅ Admin user '{username}' created successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or promote an ADMIN user")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", default="System Administrator")
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    create_or_promote_admin(args.username, args.email, args.full_name, args.password)
