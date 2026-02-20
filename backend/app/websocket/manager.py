"""WebSocket connection manager with Redis Pub/Sub for multi-instance scaling."""

import asyncio
import json
import logging
import uuid
from collections import defaultdict

from fastapi import WebSocket

from app.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections per clinic with Redis Pub/Sub broadcast.

    Local connections are tracked in-memory per process.
    Broadcasts go through Redis Pub/Sub so all instances receive them.
    """

    CHANNEL_PREFIX = "ws:clinic:"

    def __init__(self):
        self._connections: dict[uuid.UUID, list[WebSocket]] = defaultdict(list)
        self._redis = None
        self._pubsub = None
        self._listener_task: asyncio.Task | None = None

    async def _get_redis(self):
        """Lazy-init Redis connection."""
        if self._redis is None:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(
                settings.redis_url, decode_responses=True
            )
        return self._redis

    async def start_listener(self):
        """Start the Redis Pub/Sub listener background task."""
        redis = await self._get_redis()
        self._pubsub = redis.pubsub()
        # Subscribe to pattern for all clinic channels
        await self._pubsub.psubscribe(f"{self.CHANNEL_PREFIX}*")
        self._listener_task = asyncio.create_task(self._listen())
        logger.info("WebSocket Redis Pub/Sub listener started")

    async def stop_listener(self):
        """Stop the Redis Pub/Sub listener."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.punsubscribe()
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
        logger.info("WebSocket Redis Pub/Sub listener stopped")

    async def _listen(self):
        """Listen for messages from Redis and forward to local WebSocket clients."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] != "pmessage":
                    continue
                try:
                    # Channel format: ws:clinic:<uuid>
                    channel = message["channel"]
                    clinic_id_str = channel.removeprefix(self.CHANNEL_PREFIX)
                    clinic_id = uuid.UUID(clinic_id_str)
                    data = json.loads(message["data"])
                    await self._send_to_local(clinic_id, data)
                except Exception:
                    logger.exception("Error processing Redis Pub/Sub message")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Redis Pub/Sub listener crashed")

    async def _send_to_local(self, clinic_id: uuid.UUID, data: dict):
        """Send data to all local WebSocket connections for a clinic."""
        dead = []
        for ws in self._connections[clinic_id]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[clinic_id].remove(ws)

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
        """Publish message via Redis so all instances receive it."""
        try:
            redis = await self._get_redis()
            channel = f"{self.CHANNEL_PREFIX}{clinic_id}"
            await redis.publish(channel, json.dumps(data, default=str))
        except Exception:
            # Fallback: send directly to local connections if Redis is down
            logger.warning(
                "Redis Pub/Sub publish failed, falling back to local broadcast"
            )
            await self._send_to_local(clinic_id, data)

    def get_connection_count(self, clinic_id: uuid.UUID) -> int:
        return len(self._connections[clinic_id])


# Singleton instance
manager = ConnectionManager()
