import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount, WebSocketRoute

from .performance import gui_performance
from .security import gui_security

log = logging.getLogger(__name__)


class AdvancedGUI:
    def __init__(self, engine: Any, app: FastAPI) -> None:
        self.engine = engine
        self.app = app
        self._clients: set[WebSocket] = set()
        self._setup_routes()
        # Remove _setup_performance() call to avoid event loop issues
        # self._setup_performance()

    def _setup_routes(self) -> None:
        static_path = Path(__file__).parent / "static"

        # Always mount static files (FastAPI handles duplicates gracefully)
        try:
            self.app.mount("/static", StaticFiles(directory=static_path), name="static")
        except Exception:
            # Static files already mounted, continue
            pass

        # Add root route if not exists
        if not any(
            isinstance(route, APIRoute) and route.path == "/" for route in self.app.router.routes
        ):
            async def root() -> FileResponse:
                return FileResponse(static_path / "index.html")

            self.app.add_api_route("/", root, include_in_schema=False)

        # Add mobile route if not exists
        if not any(
            isinstance(route, APIRoute) and route.path == "/mobile"
            for route in self.app.router.routes
        ):
            mobile_static_path = static_path / "mobile"

            async def mobile_root() -> FileResponse:
                return FileResponse(mobile_static_path / "index.html")

            self.app.add_api_route("/mobile", mobile_root, include_in_schema=False)

        if not any(
            isinstance(route, WebSocketRoute) and route.path == "/ws"
            for route in self.app.router.routes
        ):

            async def websocket_endpoint(
                websocket: WebSocket, _token: str | None = Query(None)
            ) -> None:
                # Allow WebSocket connections without authentication for now
                # In production, you might want to add proper authentication

                await websocket.accept()
                self._clients.add(websocket)

                try:
                    while True:
                        data = await websocket.receive_text()
                        # Use the new message handling method
                        await self.handle_websocket_message(websocket, data)
                except WebSocketDisconnect:
                    log.debug("WebSocket client disconnected")
                except asyncio.CancelledError:
                    log.debug("WebSocket connection cancelled")
                    raise
                except Exception as exc:  # pragma: no cover - defensive
                    log.error("WebSocket error: %s", exc)
                finally:
                    self._clients.discard(websocket)

            self.app.add_websocket_route("/ws", websocket_endpoint)

    async def broadcast(self, message: dict[str, Any]) -> None:
        if not self._clients:
            return

        dead_clients: set[WebSocket] = set()
        payload = json.dumps(message)

        for client in self._clients:
            try:
                await client.send_text(payload)
            except Exception as exc:  # pragma: no cover - network failures
                log.warning("Dropping GUI client: %s", exc)
                dead_clients.add(client)

        self._clients.difference_update(dead_clients)

    async def run_broadcasters(self) -> None:
        if not self.engine.bus:
            log.debug("No engine bus available for GUI broadcaster")
            return

        while True:
            try:
                message = await self.engine.bus.get()
                await self.broadcast(message)
            except asyncio.CancelledError:
                log.debug("GUI broadcaster cancelled")
                raise
            except Exception as exc:  # pragma: no cover - defensive logging
                log.error("GUI broadcaster error: %s", exc)
                if self.engine.is_shutting_down:
                    break
                await asyncio.sleep(1)

    async def handle_websocket_message(self, websocket: WebSocket, message: str) -> None:
        """Handle incoming WebSocket message with security validation."""
        try:
            # Validate message
            if not gui_security.validate_websocket_message(message):
                log.warning("Invalid WebSocket message rejected")
                await websocket.send_json({"type": "error", "message": "Invalid message format"})
                return

            # Parse JSON
            data = json.loads(message)

            # Sanitize user input
            if "data" in data and isinstance(data["data"], str):
                data["data"] = gui_security.sanitize_user_input(data["data"])

            # Process message
            await self._process_websocket_message(websocket, data)

        except json.JSONDecodeError:
            log.warning("Invalid JSON in WebSocket message")
            await websocket.send_json({"type": "error", "message": "Invalid JSON format"})
        except Exception as e:
            log.error(f"Error processing WebSocket message: {e}")
            await websocket.send_json({"type": "error", "message": "Internal server error"})

    async def _process_websocket_message(self, websocket: WebSocket, data: dict[str, Any]) -> None:
        """Process validated WebSocket message."""
        message_type = data.get("type", "unknown")

        if message_type == "ping":
            await websocket.send_json({"type": "pong", "timestamp": time.time()})
        elif message_type == "get_stats":
            stats = {"connected_clients": len(self._clients)}
            await websocket.send_json({"type": "stats", "data": stats})
        elif message_type == "get_system_info":
            system_info = await self._get_system_info()
            await websocket.send_json({"type": "system_info", "data": system_info})
        else:
            # Default: broadcast to all clients
            await self.broadcast(data)

    async def _get_system_info(self) -> dict[str, Any]:
        """Get current system information."""
        return {
            "uptime": time.time() - self.engine.start_time,
            "memory_items": len(self.engine.memory),
            "phi_value": getattr(self.engine.iit_analyzer, "phi", 0.0),
            "graph_nodes": (
                len(self.engine.knowledge_graph.nodes)
                if hasattr(self.engine.knowledge_graph, "nodes")
                else 0
            ),
            "overseer_enabled": self.engine.overseer_enabled,
            "connected_clients": len(self._clients),
        }

    def get_deployment_info(self) -> dict[str, Any]:
        """Get deployment information for the GUI."""
        return {
            "version": "1.0.1",
            "environment": os.getenv("APP_ENV", "development"),
            "debug_mode": os.getenv("APP_ENV", "development").lower()
            in {"local", "development", "dev"},
            "security_enabled": True,
            "performance_monitoring": False,  # Disabled to avoid event loop issues
            "features": {
                "websocket": True,
                "file_upload": True,
                "real_time_updates": True,
                "mobile_support": True,
                "dark_mode": True,
                "analytics": True,
            },
            "limits": {
                "max_file_size": gui_security.MAX_FILE_SIZE,
                "allowed_extensions": list(gui_security.ALLOWED_EXTENSIONS),
                "rate_limit": "60 requests per minute",
                "websocket_message_limit": 10000,
            },
        }