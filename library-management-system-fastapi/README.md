# 📚 Library Management System — FastAPI Edition

Production-ready **Library Management System** built with **Python 3.12**, **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **Alembic**, strictly following **Clean Architecture**, **SOLID principles**, and core **OOP** concepts.

---

## ✨ Features

1. **User registration & JWT login** (OAuth2 password flow)
2. **Role-based authorization** — `ADMIN`, `LIBRARIAN`, `MEMBER`
3. **Book management** — add, update, delete, search (title/author/category)
4. **Issue books** — availability + borrowing-limit checks
5. **Return books** — automatic fine calculation for late returns
6. **Reports** — member loan history, system-wide overdue report

---

## 🏗️ Architecture — Clean Architecture

```
app/
├── core/                  # Framework-agnostic infrastructure concerns
│   ├── config.py           # Settings (env vars) — Pydantic BaseSettings
│   ├── security.py         # PasswordHasher, JWTHandler
│   ├── exceptions.py       # Custom exception hierarchy (AppException, ...)
│   ├── logging.py          # Centralized logging config
│   └── database.py         # SQLAlchemy engine/session/Base
│
├── models/                # SQLAlchemy ORM entities (persistence mapping only)
│   ├── base.py              # TimestampMixin (Inheritance)
│   ├── user.py, book.py, loan.py
│
├── schemas/               # Pydantic DTOs — the API "contract"
│   ├── user.py, book.py, loan.py, token.py
│
├── repositories/          # Repository Pattern — data-access abstraction
│   ├── interfaces/          # ABCs: IBookRepository, IUserRepository, ILoanRepository
│   └── *_repository.py      # Concrete SQLAlchemy implementations
│
├── services/               # Application/business logic (use cases)
│   ├── interfaces/           # ABCs: IAuthService, IBookService, ILoanService
│   └── *_service.py          # AuthService, BookService, LoanService
│
├── dependencies/           # FastAPI Dependency Injection wiring
│   ├── database.py           # get_db()
│   ├── services.py           # Composition root: repo -> service factories
│   └── auth.py               # get_current_user, RoleChecker
│
├── api/v1/                 # Thin HTTP controllers (routers)
│   ├── auth.py, books.py, loans.py, users.py, router.py
│
└── main.py                 # FastAPI app factory, middleware, exception handlers
```

### Dependency Rule

```
api (FastAPI)  --->  services (use cases)  --->  repositories (interfaces)  --->  domain (models)
      |                                                    ^
      +--------------- dependencies/services.py -----------+
                     (only place concretes are wired)
```

`services/` never import SQLAlchemy or FastAPI directly. `repositories/interfaces/` never import anything from infrastructure. This layering is followed consistently throughout the codebase.

### OOP Principles

| Principle | Where |
|---|---|
| **Encapsulation** | `PasswordHasher`/`JWTHandler` hide all bcrypt/jose details behind static methods; ORM models hide their table mapping. |
| **Inheritance** | All models inherit `TimestampMixin`; all repositories inherit `IBaseRepository[T]`; all custom exceptions inherit `AppException`. |
| **Abstraction** | `abc.ABC` + `@abstractmethod` used throughout `repositories/interfaces/` and `services/interfaces/` — callers only know the contract, not the implementation. |
| **Polymorphism** | Any `IBookRepository` implementation (Postgres today, could be Mongo/InMemory tomorrow) can be substituted wherever the interface is used; `RoleChecker.__call__` lets one class behave as different route dependencies depending on construction params. |

### SOLID Principles

| Principle | Where |
|---|---|
| **S**RP | `BookController` only handles HTTP; `BookService` only handles use-case orchestration; `BookRepository` only handles persistence; `Book` entity only describes data. |
| **O**CP | Add a `MySQLBookRepository` implementing `IBookRepository` without touching `BookService`, routes, or tests. |
| **L**SP | Any concrete repository can replace another without breaking `BookService`/`LoanService`, since they only call methods defined on the interface. |
| **I**SP | Repository interfaces are split per-entity (`IUserRepository`, `IBookRepository`, `ILoanRepository`) instead of one giant interface. |
| **D**IP | Services depend on repository **interfaces**, injected via constructor. Concrete wiring happens once, in `app/dependencies/services.py` (the composition root). |

### Design Patterns Used
- **Repository Pattern** — isolates persistence logic from business logic.
- **Dependency Injection** — FastAPI's `Depends()` + constructor injection throughout.
- **Service Layer Pattern** — use-case orchestration separate from HTTP and persistence.
- **Strategy-like role checking** — `RoleChecker` is parametrized per-route via constructor args.
- **DTO Pattern** — Pydantic schemas decouple the API contract from the ORM model.

---

## 🔧 Tech Stack

- Python 3.12
- FastAPI + Uvicorn
- PostgreSQL 16
- SQLAlchemy 2.0 (typed `Mapped[]` style)
- Alembic (migrations)
- Pydantic v2 / pydantic-settings
- python-jose (JWT) + passlib/bcrypt (password hashing)
- Docker & Docker Compose
- Pytest + httpx (testing, in-memory SQLite)

---

## 🚀 Getting Started

### Option A — Docker (recommended)

```bash
cp .env.example .env
# edit .env and set a strong SECRET_KEY, e.g.: openssl rand -hex 32

docker-compose up --build
```

This starts PostgreSQL, runs Alembic migrations automatically, then launches the API at **http://localhost:8000**.
Interactive docs: **http://localhost:8000/docs**

### Option B — Local (without Docker)

```bash
python3.12 -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env -> point DATABASE_URL at your local PostgreSQL instance

# Create the database first, e.g.:
createdb library_db

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

---

## 🧪 Running Tests

Tests run against an **in-memory SQLite** database (no PostgreSQL required), so they're fast and isolated:

```bash
pip install -r requirements.txt
pytest -v
pytest --cov=app --cov-report=term-missing   # with coverage
```

Test suite covers:
- Registration (success, duplicate username/email, weak password/invalid email)
- Login (success, wrong password, nonexistent user)
- JWT validation (`/me` with/without/invalid token)
- Role-based authorization (member forbidden from book CRUD; admin allowed)
- Book CRUD + search + duplicate ISBN handling
- Issue book (availability check, borrowing-limit enforcement, role restriction)
- Return book (on-time = no fine, late = fine calculated correctly)
- Reports (own history, overdue report, admin-only access)

---

## 📡 API Reference

All endpoints are prefixed with `/api/v1`.

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | Public | Register a new user (always created as `MEMBER`) |
| POST | `/auth/login` | Public | OAuth2 form login, returns access + refresh JWT |
| GET | `/auth/me` | Any | Current user's profile |

### Users (admin)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/users` | ADMIN | List all users |
| GET | `/users/{id}` | ADMIN | Get a single user |

### Books
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/books` | LIBRARIAN/ADMIN | Add a book |
| GET | `/books?title=&author=&category=` | Any | Search/list books |
| GET | `/books/{id}` | Any | Get a book |
| PUT | `/books/{id}` | LIBRARIAN/ADMIN | Update a book |
| DELETE | `/books/{id}` | LIBRARIAN/ADMIN | Delete a book |

### Loans
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/loans/issue` | LIBRARIAN/ADMIN | Issue a book `{book_id, member_id}` |
| POST | `/loans/return` | LIBRARIAN/ADMIN | Return a book `{book_id, member_id}` (returns fine) |
| GET | `/loans?member_id=&book_id=&status=` | LIBRARIAN/ADMIN | Filter all loans |
| GET | `/loans/overdue` | LIBRARIAN/ADMIN | Overdue books report |
| GET | `/loans/my-history` | Any | Own loan history |
| GET | `/loans/member/{id}` | LIBRARIAN/ADMIN | Any member's loan history |

### Example: full flow with curl

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","full_name":"Alice","password":"SecurePass123"}'

# 2. Login (OAuth2 form-encoded)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=alice&password=SecurePass123"
# -> copy the access_token from the response

# 3. Call a protected endpoint
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

> To test ADMIN/LIBRARIAN-only endpoints, promote a user's `role` directly in the
> database (e.g. `UPDATE users SET role = 'ADMIN' WHERE username = 'alice';`),
> since self-registration always creates a `MEMBER`.

### Bootstrapping the first admin

Self-registration always creates a `MEMBER` (by design, to prevent privilege
escalation through the public API). Use the included script to create or
promote your first admin account:

```bash
# Docker:
docker-compose exec api python scripts/create_admin.py \
  --username admin --email admin@library.com --password ChangeMe123

# Local:
python scripts/create_admin.py --username admin --email admin@library.com --password ChangeMe123
```

---

## 🗃️ Database Migrations (Alembic)

```bash
# Generate a new migration after changing models/
alembic revision --autogenerate -m "add reservations table"

# Apply migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

The included `alembic/versions/0001_initial_migration.py` creates the `users`, `books`, and `loans` tables with their enums, indexes, and check constraints.

---

## ⚙️ Environment Variables

See `.env.example` for the full list. Key ones:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy connection string |
| `SECRET_KEY` | JWT signing secret, must be changed in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime |
| `LOAN_PERIOD_DAYS` | Default loan period (14 days) |
| `FINE_PER_DAY` | Late-return fine rate |
| `MAX_ACTIVE_LOANS_PER_MEMBER` | Borrowing limit per member (3) |

---

## 📁 Business Rules Summary

- A member may hold at most **3** active loans at once (`MAX_ACTIVE_LOANS_PER_MEMBER`).
- Loan period is **14 days** (`LOAN_PERIOD_DAYS`) from issue date.
- Late fine is **10 currency units/day** (`FINE_PER_DAY`) past the due date.
- A book can only be issued while `available_copies > 0`.
- `total_copies` can never be reduced below the number of copies currently on loan.

---

## 🔐 Security Notes

- Passwords are hashed with **bcrypt** (via passlib), never stored in plaintext.
- JWT access tokens are short-lived (default 60 min); refresh tokens last 7 days.
- All error responses go through a single global exception handler for consistent, non-leaky error messages.
- The app runs as a **non-root user** inside its Docker container.
