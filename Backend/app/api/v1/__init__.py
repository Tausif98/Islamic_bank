from fastapi import APIRouter
from app.api.v1 import customers, accounts, transactions, websocket

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(customers.router)
api_router.include_router(accounts.router)
api_router.include_router(transactions.router)
api_router.include_router(websocket.router)