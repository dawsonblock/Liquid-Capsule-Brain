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

log = logging.getLogger(__name__)


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
            websocket: WebSocket, token: str | None = Query(default=None)
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
                    if getattr(self.engine, "bus", None) is not None:
                        await self.engine.bus.put(
                            {
                                "type": "user_chat_message",
                                "payload": {"text": data},
                            }
                        )
            except WebSocketDisconnect:
                self._clients.discard(websocket)
            except Exception as exc:  # pragma: no cover - defensive logging
                log.error("WebSocket error: %s", exc)
                self._clients.discard(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        if not self._clients:
            return

        dead_clients: set[WebSocket] = set()
        payload = json.dumps(message)
        for client in self._clients:
            try:
                await client.send_text(payload)
            except Exception:  # pragma: no cover - best effort cleanup
                dead_clients.add(client)

        self._clients -= dead_clients

    async def run_broadcasters(self) -> None:
        if getattr(self.engine, "bus", None) is None:
            return

        while True:
            try:
                message = await self.engine.bus.get()
                await self.broadcast(message)
            except Exception as exc:  # pragma: no cover - defensive logging
                log.error("GUI broadcaster error: %s", exc)
                await asyncio.sleep(1)
