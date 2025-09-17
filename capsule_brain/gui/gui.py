"""Web user interface integration for the Capsule Brain."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ..security.secrets import SecretManager

logger = logging.getLogger(__name__)


class AdvancedGUI:
    def __init__(self, engine: Any, app: FastAPI) -> None:
        self.engine = engine
        self.app = app
        self._clients: set[WebSocket] = set()
        self._setup_routes()

    def _setup_routes(self) -> None:
        static_path = Path(__file__).parent / "static"
        self.app.mount("/static", StaticFiles(directory=static_path), name="static")

        @self.app.get("/", include_in_schema=False)
        async def root() -> FileResponse:
            return FileResponse(static_path / "index.html")

        @self.app.websocket("/ws")
        async def websocket_endpoint(
            websocket: WebSocket, token: str | None = Query(None)
        ) -> None:
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
                            {"type": "user_chat_message", "payload": {"text": data}}
                        )
            except WebSocketDisconnect:
                self._clients.discard(websocket)
            except Exception:  # pragma: no cover - defensive logging
                logger.exception("WebSocket error")
                self._clients.discard(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        if not self._clients:
            return
        dead: set[WebSocket] = set()
        payload = json.dumps(message)
        for client in self._clients:
            try:
                await client.send_text(payload)
            except Exception:  # pragma: no cover - defensive logging
                dead.add(client)
        self._clients -= dead

    async def run_broadcasters(self) -> None:
        if not self.engine.bus:
            return
        while True:
            try:
                message = await self.engine.bus.get()
                await self.broadcast(message)
            except Exception:  # pragma: no cover - defensive logging
                logger.exception("GUI broadcaster error")
                await asyncio.sleep(1)
