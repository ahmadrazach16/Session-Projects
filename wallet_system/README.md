# Ledger — Digital Wallet & Money Transfer System

A full-stack wallet/transfer system built exactly to the assignment spec:
**Client → API/Controller Layer → Business/Service Layer → Repository/Data Access Layer → Database**

## Stack
- **Backend:** Python 3 + Flask + SQLite (no external DB server needed)
- **Auth:** JWT (PyJWT) + hashed passwords (Werkzeug)
- **Frontend:** Plain HTML/CSS/JS (no build step) — served directly by Flask

## Project structure
```
wallet_system/
├── backend/
│   ├── app.py                     # Flask entrypoint, wires everything together
│   ├── api/                       # Controller layer — HTTP only, no business rules
│   │   ├── auth_routes.py
│   │   ├── wallet_routes.py
│   │   ├── admin_routes.py
│   │   └── auth_middleware.py     # JWT auth decorators
│   ├── services/                  # Business/Service layer — ALL rules live here
│   │   ├── auth_service.py
│   │   ├── wallet_service.py      # deposit / withdraw rules
│   │   ├── transfer_service.py    # atomic, idempotent transfer rules
│   │   ├── admin_wallet_service.py
│   │   ├── transaction_service.py
│   │   └── exceptions.py
│   ├── repositories/               # Data Access layer — raw SQL only
│   │   ├── user_repository.py
│   │   ├── wallet_repository.py
│   │   ├── transaction_repository.py
│   │   └── config_repository.py
│   └── models/
│       └── database.py            # schema + connection
└── frontend/
    ├── index.html
    ├── styles.css
    └── app.js
```

## How to run

```bash
cd backend
pip install flask pyjwt werkzeug   # only if not already installed
python3 app.py
```

Then open **http://localhost:5000** in your browser. The Flask app serves both
the API (`/api/...`) and the frontend, so there's nothing else to start.

A default admin account is seeded automatically:
- **Email:** admin@wallet.com
- **Password:** admin123

## What's implemented (mapped to the assignment doc)

- **Layered architecture** — API layer never contains business logic; it only
  calls into Services, which call Repositories, which touch the DB.
- **Roles** — Customer (wallets, deposit, withdraw, transfer, history) and
  Admin (view users/wallets, freeze/unfreeze, adjust balance, investigate
  failed transactions).
- **One active wallet per currency** — enforced with a DB unique constraint
  (`user_id`, `currency`) plus a service-layer check.
- **Wallet statuses** — ACTIVE / FROZEN / CLOSED; frozen wallets reject all
  deposit/withdraw/transfer calls.
- **Deposit & withdrawal** — validates wallet ownership, active status,
  positive amount, single/daily limits; withdrawal never allows a negative
  balance.
- **Transfer** — implements all 8 rules from the spec (sender/receiver
  exist, no self-transfer, both active, positive amount, sufficient balance,
  daily limit, and full atomicity via `BEGIN IMMEDIATE` / commit / rollback
  so a partial update — debit without credit — is impossible).
- **Idempotency key** — `Idempotency-Key` header; a repeated request with the
  same key returns the original transaction instead of transferring twice.
- **Transaction reference** — generated application-side as
  `TXN-YYYYMMDD-XXXXXX`, uniqueness guaranteed by a DB `UNIQUE` constraint
  with retry-on-collision.
- **Transaction history** — pagination, filter by type/status/date
  range/amount range/reference search.
- **Daily limits** — centralized in a `wallet_configuration` table/service,
  not hard-coded across the codebase; admins can update them via
  `PUT /api/admin/config`.
- **Wallet freeze/unfreeze** and **controlled balance adjustment** — the
  admin can never write a raw balance; adjustments go through a transactional,
  auditable service call that always creates a transaction record.
- **Transaction state machine** — PENDING/COMPLETED/FAILED/CANCELLED, with
  invalid transitions (e.g. COMPLETED → FAILED) never produced by the code.

## Notes / things you may want to extend
- SQLite is used for simplicity — the Repository layer is the only place
  that would need to change to swap in Postgres/MySQL.
- The `transactions` table also stores `ADJUSTMENT` as a type, alongside the
  three types in the original document, so admin balance corrections are
  auditable like everything else.
