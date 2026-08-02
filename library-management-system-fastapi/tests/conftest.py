"""
Shared pytest fixtures.

Tests run against an in-memory SQLite database instead of PostgreSQL -
this keeps unit tests fast and dependency-free while still exercising
the full ORM/repository/service stack. The `get_db` dependency is
overridden so the FastAPI app under test uses this SQLite session
instead of the real Postgres connection pool.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.dependencies.database import get_db
from app.main import app

# In-memory SQLite shared across the whole test session via StaticPool
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh schema for every test function, then tears it down."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient wired to the SQLite test session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def registered_member(client):
    """Registers and returns a MEMBER user's auth headers + id."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "member1",
            "email": "member1@example.com",
            "full_name": "Member One",
            "password": "SecurePass123",
        },
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "member1", "password": "SecurePass123"},
    )
    token = login_resp.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return {"headers": {"Authorization": f"Bearer {token}"}, "id": me.json()["id"]}


@pytest.fixture
def admin_user(client, db_session):
    """
    Registers a user then promotes them to ADMIN directly via the DB
    session (simulating a seeded/pre-existing admin account), and logs in.
    """
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin1",
            "email": "admin1@example.com",
            "full_name": "Admin One",
            "password": "SecurePass123",
        },
    )
    from app.models.user import User, UserRole

    user = db_session.query(User).filter(User.username == "admin1").first()
    user.role = UserRole.ADMIN
    db_session.commit()

    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin1", "password": "SecurePass123"},
    )
    token = login_resp.json()["access_token"]
    return {"headers": {"Authorization": f"Bearer {token}"}}
