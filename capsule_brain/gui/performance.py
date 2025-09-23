"""Performance optimizations for the GUI system."""

import asyncio
import logging
import time
from typing import Any

from fastapi import WebSocket

log = logging.getLogger(__name__)


class GUIPerformanceManager:
    """Performance manager for GUI components."""

    def __init__(self) -> None:
        """Initialize GUI performance manager."""
        self.message_queue: asyncio.Queue[dict[str, Any]] | None = None
        self.broadcast_queue: asyncio.Queue[dict[str, Any]] | None = None
        self.connected_clients: set[WebSocket] = set()
        self.message_stats: dict[str, int] = {
            "total_messages": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "queue_overflows": 0,
        }
        self.performance_metrics: dict[str, float] = {
            "avg_message_processing_time": 0.0,
            "avg_broadcast_time": 0.0,
            "queue_size": 0.0,
        }
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure queues are initialized in the current event loop."""
        if not self._initialized:
            self.message_queue = asyncio.Queue(maxsize=1000)
            self.broadcast_queue = asyncio.Queue(maxsize=500)
            self._initialized = True

    async def add_message(self, message: dict[str, Any]) -> bool:
        """Add message to processing queue.

        Args:
            message: Message to add

        Returns:
            True if added successfully, False if queue is full
        """
        self._ensure_initialized()
        try:
            self.message_queue.put_nowait(message)
            self.message_stats["total_messages"] += 1
            return True
        except asyncio.QueueFull:
            self.message_stats["queue_overflows"] += 1
            log.warning("Message queue overflow - dropping message")
            return False

    async def add_broadcast(self, message: dict[str, Any]) -> bool:
        """Add message to broadcast queue.

        Args:
            message: Message to broadcast

        Returns:
            True if added successfully, False if queue is full
        """
        self._ensure_initialized()
        try:
            self.broadcast_queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            log.warning("Broadcast queue overflow - dropping message")
            return False

    async def process_messages(self) -> None:
        """Process messages from the queue."""
        self._ensure_initialized()
        while True:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)

                start_time = time.time()
                await self._process_single_message(message)
                processing_time = time.time() - start_time

                # Update performance metrics
                self._update_processing_metrics(processing_time)

            except TimeoutError:
                # No messages, continue
                continue
            except Exception as e:
                log.error(f"Error processing message: {e}")
                self.message_stats["messages_failed"] += 1

    async def broadcast_messages(self) -> None:
        """Broadcast messages to all connected clients."""
        self._ensure_initialized()
        while True:
            try:
                # Wait for broadcast message with timeout
                message = await asyncio.wait_for(self.broadcast_queue.get(), timeout=1.0)

                start_time = time.time()
                await self._broadcast_to_clients(message)
                broadcast_time = time.time() - start_time

                # Update performance metrics
                self._update_broadcast_metrics(broadcast_time)

            except TimeoutError:
                # No broadcasts, continue
                continue
            except Exception as e:
                log.error(f"Error broadcasting message: {e}")

    async def _process_single_message(self, message: dict[str, Any]) -> None:
        """Process a single message.

        Args:
            message: Message to process
        """
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = time.time()

        # Add to broadcast queue for real-time updates
        await self.add_broadcast(message)

    async def _broadcast_to_clients(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients.

        Args:
            message: Message to broadcast
        """
        if not self.connected_clients:
            return

        # Prepare message for WebSocket
        ws_message = {
            "type": "update",
            "data": message,
            "timestamp": time.time(),
        }

        # Send to all connected clients
        disconnected_clients = set()
        for client in self.connected_clients:
            try:
                await client.send_json(ws_message)
                self.message_stats["messages_sent"] += 1
            except Exception as e:
                log.warning(f"Failed to send message to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            self.connected_clients.discard(client)

    def _update_processing_metrics(self, processing_time: float) -> None:
        """Update message processing metrics.

        Args:
            processing_time: Time taken to process message
        """
        # Exponential moving average
        alpha = 0.1
        self.performance_metrics["avg_message_processing_time"] = (
            alpha * processing_time
            + (1 - alpha) * self.performance_metrics["avg_message_processing_time"]
        )

    def _update_broadcast_metrics(self, broadcast_time: float) -> None:
        """Update broadcast metrics.

        Args:
            broadcast_time: Time taken to broadcast message
        """
        # Exponential moving average
        alpha = 0.1
        self.performance_metrics["avg_broadcast_time"] = (
            alpha * broadcast_time + (1 - alpha) * self.performance_metrics["avg_broadcast_time"]
        )

    def add_client(self, client: WebSocket) -> None:
        """Add a new client connection.

        Args:
            client: WebSocket client to add
        """
        self.connected_clients.add(client)
        log.info(f"Client connected. Total clients: {len(self.connected_clients)}")

    def remove_client(self, client: WebSocket) -> None:
        """Remove a client connection.

        Args:
            client: WebSocket client to remove
        """
        self.connected_clients.discard(client)
        log.info(f"Client disconnected. Total clients: {len(self.connected_clients)}")

    def get_performance_stats(self) -> dict[str, Any]:
        """Get current performance statistics.

        Returns:
            Dictionary containing performance metrics
        """
        current_time = time.time()

        # Update queue size
        if self._initialized:
            self.performance_metrics["queue_size"] = (
                self.message_queue.qsize() + self.broadcast_queue.qsize()
            )
        else:
            self.performance_metrics["queue_size"] = 0

        # Cleanup old data periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_data()
            self.last_cleanup = current_time

        return {
            "performance_metrics": self.performance_metrics.copy(),
            "message_stats": self.message_stats.copy(),
            "connected_clients": len(self.connected_clients),
            "queue_sizes": {
                "message_queue": self.message_queue.qsize() if self._initialized else 0,
                "broadcast_queue": self.broadcast_queue.qsize() if self._initialized else 0,
            },
        }

    def _cleanup_old_data(self) -> None:
        """Cleanup old performance data."""
        # Reset counters periodically to prevent overflow
        if self.message_stats["total_messages"] > 1000000:
            self.message_stats["total_messages"] = 0
            self.message_stats["messages_sent"] = 0
            self.message_stats["messages_failed"] = 0
            self.message_stats["queue_overflows"] = 0

    async def start_performance_monitoring(self) -> None:
        """Start performance monitoring tasks."""
        # Start message processing task
        asyncio.create_task(self.process_messages())

        # Start broadcast task
        asyncio.create_task(self.broadcast_messages())

        log.info("GUI performance monitoring started")

    def optimize_for_mobile(self, user_agent: str) -> dict[str, Any]:
        """Optimize GUI settings for mobile devices.

        Args:
            user_agent: User agent string

        Returns:
            Optimization settings for mobile
        """
        is_mobile = any(
            mobile_indicator in user_agent.lower()
            for mobile_indicator in ["mobile", "android", "iphone", "ipad"]
        )

        if is_mobile:
            return {
                "reduced_animations": True,
                "smaller_charts": True,
                "touch_optimized": True,
                "reduced_data_updates": True,
                "cache_aggressive": True,
            }

        return {
            "reduced_animations": False,
            "smaller_charts": False,
            "touch_optimized": False,
            "reduced_data_updates": False,
            "cache_aggressive": False,
        }


# Global performance manager instance
gui_performance = GUIPerformanceManager()
