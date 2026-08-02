"""
Aggregates all v1 routers into a single APIRouter, mounted once in
app/main.py. Adding a new resource (e.g. reservations) means creating
a new router module and registering it here - no other file changes
(Open/Closed Principle).
"""
from fastapi import APIRouter

from app.api.v1 import auth, books, loans, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(books.router)
api_router.include_router(loans.router)
