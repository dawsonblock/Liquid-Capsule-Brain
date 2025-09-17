from fastapi.testclient import TestClient

from capsule_brain.api.server import app


def test_gui_root_and_websocket() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("ping")
            # If the server accepted the connection and we can send a message
            # without raising, the GUI endpoint is responsive.
