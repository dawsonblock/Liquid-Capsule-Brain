import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount, WebSocketRoute

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

        if not any(isinstance(route, Mount) and route.path == "/static" for route in self.app.router.routes):
            self.app.mount("/static", StaticFiles(directory=static_path), name="static")

        if not any(isinstance(route, APIRoute) and route.path == "/" for route in self.app.router.routes):

            async def root() -> FileResponse:
                return FileResponse(static_path / "index.html")

            self.app.add_api_route("/", root, include_in_schema=False)

        # Add mobile route
        if not any(isinstance(route, APIRoute) and route.path == "/mobile" for route in self.app.router.routes):
            mobile_static_path = static_path / "mobile"
            
            async def mobile_root() -> FileResponse:
                return FileResponse(mobile_static_path / "index.html")

            self.app.add_api_route("/mobile", mobile_root, include_in_schema=False)

        if not any(isinstance(route, WebSocketRoute) and route.path == "/ws" for route in self.app.router.routes):

            async def websocket_endpoint(
                websocket: WebSocket, token: str | None = Query(None)
            ) -> None:
                # Allow WebSocket connections without authentication for now
                # In production, you might want to add proper authentication
                pass

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
                    log.debug("WebSocket client disconnected")
                except asyncio.CancelledError:
                    log.debug("WebSocket connection cancelled")
                    raise
                except Exception as exc:  # pragma: no cover - defensive logging
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
