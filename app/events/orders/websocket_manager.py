import asyncio
import logging
import uuid
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """Manages WebSocket connections for realtime order tracking"""

    def __init__(self):
        self.active_connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)
        self.order_subscriptions: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)
        self.websocket_to_user: dict[WebSocket, uuid.UUID] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID) -> None:
        """Register a new WebSocket connection for a user"""
        await websocket.accept()
        async with self._lock:
            self.active_connections[user_id].add(websocket)
            self.websocket_to_user[websocket] = user_id
            logger.info(f"User {user_id} connected via WebSocket")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection"""
        user_id = self.websocket_to_user.get(websocket)
        if not user_id:
            logger.warning("WebSocket connection not found in registry")
            return

        async with self._lock:
            self.active_connections[user_id].discard(websocket)

            for order_id in list(self.order_subscriptions.keys()):
                if websocket in self.order_subscriptions[order_id]:
                    self.order_subscriptions[order_id].discard(websocket)
                    logger.info(f"User {user_id} unsubscribed from order {order_id}")

            del self.websocket_to_user[websocket]
            logger.info(f"User {user_id} disconnected from WebSocket")

        try:
            await websocket.close()
            logger.info(f"WebSocket connection closed for user {user_id}")
        except Exception as e:
            logger.debug(f"Error closing WebSocket for user {user_id}: {e}")

    async def subscribe_to_order(
        self, websocket: WebSocket, order_id: uuid.UUID
    ) -> None:
        """Subscribe a WebSocket connection to updates for a specific order"""
        user_id = self.websocket_to_user.get(websocket)
        if not user_id:
            logger.warning("WebSocket connection not found in registry")
            return

        async with self._lock:
            self.order_subscriptions[order_id].add(websocket)
            logger.info(f"User {user_id} subscribed to order {order_id}")

    async def broadcast_to_order(self, order_id: uuid.UUID, message: dict) -> None:
        """Send a message to all WebSocket connections subscribed to an order."""
        pass
