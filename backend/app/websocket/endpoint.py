"""WebSocket endpoint with JWT authentication."""

import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.security import decode_token
from app.models.user import User
from app.websocket.manager import manager

router = APIRouter()


async def _authenticate_ws(token: str) -> User | None:
    """Validate JWT and return user."""
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except InvalidTokenError:
        return None

    async with async_session_factory() as db:
        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            return None
        return user


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default=""),
):
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    user = await _authenticate_ws(token)
    if user is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    clinic_id = user.clinic_id
    await manager.connect(websocket, clinic_id)

    try:
        while True:
            # Keep connection alive, handle client messages if needed
            data = await websocket.receive_text()
            # Could handle ping/pong or client events here
    except WebSocketDisconnect:
        manager.disconnect(websocket, clinic_id)
