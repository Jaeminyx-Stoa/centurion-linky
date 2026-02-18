"""WebSocket connection manager for real-time clinic dashboard updates."""

import uuid
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections per clinic."""

    def __init__(self):
        self._connections: dict[uuid.UUID, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, clinic_id: uuid.UUID):
        await websocket.accept()
        self._connections[clinic_id].append(websocket)
        await websocket.send_json({
            "type": "connected",
            "clinic_id": str(clinic_id),
        })

    def disconnect(self, websocket: WebSocket, clinic_id: uuid.UUID):
        if websocket in self._connections[clinic_id]:
            self._connections[clinic_id].remove(websocket)

    async def broadcast_to_clinic(self, clinic_id: uuid.UUID, data: dict):
        dead = []
        for ws in self._connections[clinic_id]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[clinic_id].remove(ws)

    def get_connection_count(self, clinic_id: uuid.UUID) -> int:
        return len(self._connections[clinic_id])


# Singleton instance
manager = ConnectionManager()
