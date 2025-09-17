"""FastAPI GUI utilities for the Capsule Brain project."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ..security.secrets import SecretManager

if TYPE_CHECKING:  # pragma: no cover - used for type checking only
    from capsule_brain.core.capsule_engine import CapsuleEngine


log = logging.getLogger(__name__)


class AdvancedGUI:
    """Register SPA routes and manage websocket broadcasts."""

    def __init__(self, engine: CapsuleEngine, app: FastAPI) -> None:
        self.engine = engine
        self.app = app
        self._clients: set[WebSocket] = set()
        self._static_path = Path(__file__).parent / "static"

        self._ensure_routes()
        self.app.state.gui_manager = self

    def _ensure_routes(self) -> None:
        if getattr(self.app.state, "_gui_routes_registered", False):
            return

        self.app.mount("/static", StaticFiles(directory=self._static_path), name="static")

        @self.app.get("/", include_in_schema=False)
        async def root() -> FileResponse:
            return FileResponse(self._static_path / "index.html")

        @self.app.websocket("/ws")
        async def websocket_endpoint(
            websocket: WebSocket,
            token: str | None = Query(None),
        ) -> None:
            manager: AdvancedGUI | None = getattr(self.app.state, "gui_manager", None)
            if manager is None:
                await websocket.close(code=1013, reason="GUI offline")
                return
            await manager.handle_websocket(websocket, token)

        self.app.state._gui_routes_registered = True

    async def handle_websocket(self, websocket: WebSocket, token: str | None) -> None:
        admin_env = SecretManager.get_secret("ADMIN_API_KEY")
        if admin_env and token != admin_env:
            await websocket.close(code=4003, reason="Invalid authentication token")
            return

        await websocket.accept()
        self._clients.add(websocket)

        try:
            while True:
                data = await websocket.receive_text()
                if self.engine.bus:
                    await self.engine.bus.put(
                        {
                            "type": "user_chat_message",
                            "payload": {"text": data},
                        }
                    )
        except WebSocketDisconnect:
            self._clients.discard(websocket)
        except asyncio.CancelledError:
            self._clients.discard(websocket)
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            log.error("WebSocket error: %s", exc)
            self._clients.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        if not self._clients:
            return

        dead: set[WebSocket] = set()
        payload = json.dumps(message)

        for client in list(self._clients):
            try:
                await client.send_text(payload)
            except Exception:  # pragma: no cover - defensive cleanup
                dead.add(client)

        self._clients -= dead

    async def run_broadcasters(self) -> None:
        if not self.engine.bus:
            return

        while True:
            try:
                message = await self.engine.bus.get()
                await self.broadcast(message)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive logging
                log.error("GUI broadcaster error: %s", exc)
                await asyncio.sleep(1)

    async def close(self) -> None:
        """Close any active client sessions when the server shuts down."""

        for client in list(self._clients):
            with suppress(Exception):
                await client.close(code=1001, reason="Server shutting down")
        self._clients.clear()
        if getattr(self.app.state, "gui_manager", None) is self:
            self.app.state.gui_manager = None
