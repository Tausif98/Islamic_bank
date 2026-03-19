"""
WebSocket handler for real-time account updates.

Flow:
  Client connects → WS /ws/{account_id}?token=<JWT>
  Server verifies JWT → subscribes to Redis channel 'account:{account_id}'
  When any transaction completes → Redis receives publish → forwarded to client

This way, the HTTP transaction endpoints don't need to know about WebSocket clients.
Redis pub/sub acts as the bridge (decoupled).
"""
import json
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from app.core.security import decode_access_token
from app.core.redis import get_pubsub
from app.db.repositories.account_repo import account_repo
from app.db.repositories.customer_repo import customer_repo

router = APIRouter(tags=["WebSocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/{account_id}")
async def account_websocket(
    websocket: WebSocket,
    account_id: str,
    token: str = Query(...),    # JWT passed as query param (WebSocket can't send headers easily)
):
    # Auth check before accepting connection
    try:
        payload = decode_access_token(token)
        customer_id = payload.get("sub")
        customer = await customer_repo.get_by_id(customer_id)
        if not customer:
            await websocket.close(code=4001)
            return
    except HTTPException:
        await websocket.close(code=4001)
        return

    # Verify account ownership
    account = await account_repo.get_by_id(account_id)
    if not account:
        await websocket.close(code=4004)
        return

    await websocket.accept()
    logger.info(f"WebSocket connected: customer={customer_id}, account={account_id}")

    # Subscribe to Redis channel for this specific account
    pubsub = await get_pubsub()
    channel = f"account:{account_id}"
    await pubsub.subscribe(channel)

    try:
        # Send initial balance snapshot
        await websocket.send_json({
            "type": "connected",
            "account_id": account_id,
            "balance": str(account.balance),
            "currency": account.currency,
        })

        # Listen for Redis messages and forward to WebSocket client
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: account={account_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()