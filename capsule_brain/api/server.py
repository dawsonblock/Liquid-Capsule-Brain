import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import (
    Body,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from capsule_brain.api.dependencies import (
    attach_engine,
    detach_engine,
    get_engine,
    peek_engine,
)
from capsule_brain.core.capsule_engine import CapsuleEngine
from capsule_brain.gui.gui import AdvancedGUI
from capsule_brain.observability.metrics import (
    record_llm_tokens,
    setup_metrics,
)
from capsule_brain.security.admin import require_admin_token

log = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    capsule_engine = CapsuleEngine()
    attach_engine(app, capsule_engine)
    await capsule_engine.start_background_tasks(app)
    gui = AdvancedGUI(capsule_engine, app)
    app.state.gui = gui
    broadcaster_task = asyncio.create_task(app.state.gui.run_broadcasters())
    log.info("Engine started.")
    try:
        yield
    finally:
        broadcaster_task.cancel()
        try:
            await broadcaster_task
        except asyncio.CancelledError:
            pass
        attached = detach_engine(app)
        if attached:
            await attached.shutdown()


app = FastAPI(
    title="Capsule Brain Supreme AGI",
    version="1.0.1",
    lifespan=app_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Prometheus metrics before app startup
setup_metrics(app)

EngineDep = Annotated[CapsuleEngine, Depends(get_engine)]


class AskRequest(BaseModel):
    q: str


@app.get("/healthz", dependencies=[Depends(require_admin_token)])
async def healthz() -> dict[str, Any]:
    return {"ok": True}


@app.get("/ready", dependencies=[Depends(require_admin_token)])
async def ready(request: Request) -> dict[str, Any]:
    return {"ready": peek_engine(request.app) is not None}


@app.get("/state/summary")
async def state_summary(engine: EngineDep) -> dict[str, Any]:
    return engine.get_state_summary()


@app.post("/ask")
async def ask(
    engine: EngineDep,
    payload: AskRequest | None = Body(default=None),  # noqa: B008
    q: str | None = None,
) -> dict[str, Any]:
    question = payload.q if (payload and getattr(payload, "q", None)) else q
    if not question:
        raise HTTPException(
            status_code=422,
            detail="Missing 'q' in body or query",
        )
    engine.add_memory("user", question)
    engine.belief_state_manager.current_query = question

    # Generate LLM response using DeepSeek
    llm_response = await engine.belief_state_manager.generate_llm_response()

    # Add the response to memory
    if llm_response.get("text"):
        engine.add_memory("assistant", llm_response["text"])

    # Record DeepSeek token usage metrics if present
    usage = llm_response.get("usage") or {}
    try:
        prompt_tokens = usage.get("prompt_tokens", 0) or 0
        completion_tokens = usage.get("completion_tokens", 0) or 0
        model_name = str(llm_response.get("model", "deepseek-chat"))
        if (prompt_tokens or completion_tokens) and model_name:
            record_llm_tokens(
                "deepseek",
                model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
    except Exception:  # defensive metrics guard
        pass

    context, system_prompt = (
        engine.belief_state_manager.synthesize_context_for_llm()
    )
    return {
        "ack": True,
        "context": context,
        "system": system_prompt,
        "llm_response": llm_response,
    }


@app.post("/ask_with_document")
async def ask_with_document(
    engine: EngineDep,
    file: UploadFile = File(...),  # noqa: B008
    q: str = Form("Document question"),
) -> dict[str, Any]:
    # Minimal handling: record the file reference and generate a response
    q_value = q or "Document question"
    engine.add_memory("user", f"{q_value}\n[Attached file: {file.filename}]")
    engine.belief_state_manager.current_query = q_value
    llm_response = await engine.belief_state_manager.generate_llm_response()
    if llm_response.get("text"):
        engine.add_memory("assistant", llm_response["text"])
    # Record DeepSeek token usage metrics if present
    usage = llm_response.get("usage") or {}
    try:
        prompt_tokens = usage.get("prompt_tokens", 0) or 0
        completion_tokens = usage.get("completion_tokens", 0) or 0
        model_name = str(llm_response.get("model", "deepseek-chat"))
        if (prompt_tokens or completion_tokens) and model_name:
            record_llm_tokens(
                "deepseek",
                model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
    except Exception:
        pass
    context, system_prompt = (
        engine.belief_state_manager.synthesize_context_for_llm()
    )
    return {
        "ack": True,
        "context": context,
        "system": system_prompt,
        "llm_response": llm_response,
    }


@app.get("/debug/env")
async def debug_env() -> dict[str, Any]:
    """Debug endpoint to check environment variables."""
    admin_val = os.getenv("ADMIN_TOKEN")
    return {
        "admin_token_set": bool(admin_val),
        "admin_token_value": (
            (admin_val[:10] + "...") if admin_val else "NOT_SET"
        ),
        "deepseek_key_set": bool(os.getenv("DEEPSEEK_API_KEY")),
        "app_env": os.getenv("APP_ENV", "NOT_SET"),
        "app_profile": os.getenv("APP_PROFILE", "NOT_SET"),
    }


@app.post("/graph/edge", dependencies=[Depends(require_admin_token)])
async def add_edge(
    source: str,
    target: str,
    engine: EngineDep,
    relation: str = "related_to",
) -> dict[str, Any]:
    engine.add_graph_edge(source, target, relation)
    return {
        "ok": True,
        "graph": {
            "nodes": engine.knowledge_graph.number_of_nodes(),
            "edges": engine.knowledge_graph.number_of_edges(),
        },
    }


@app.post("/overseer/enable", dependencies=[Depends(require_admin_token)])
async def enable_overseer(engine: EngineDep) -> dict[str, Any]:
    """Enable the AI overseer."""
    engine.enable_overseer()
    if not engine.overseer:
        await engine.start_overseer()
    return {"ok": True, "overseer_enabled": engine.overseer_enabled}


@app.post("/overseer/disable", dependencies=[Depends(require_admin_token)])
async def disable_overseer(engine: EngineDep) -> dict[str, Any]:
    """Disable the AI overseer."""
    engine.disable_overseer()
    await engine.stop_overseer()
    return {"ok": True, "overseer_enabled": engine.overseer_enabled}


@app.get("/overseer/status")
async def overseer_status(engine: EngineDep) -> dict[str, Any]:
    """Get the current status of the AI overseer."""
    return {
        "overseer_enabled": engine.overseer_enabled,
        "overseer_running": engine.overseer is not None,
    }
