"""FastAPI application wiring for the Capsule Brain service."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from capsule_brain.core.capsule_engine import CapsuleEngine
from capsule_brain.gui.gui import AdvancedGUI
from capsule_brain.observability.metrics import (
    MetricsMiddleware,
    router as metrics_router,
)

log = logging.getLogger(__name__)

app = FastAPI(title="Capsule Brain Supreme AGI", version="1.0.1")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics
app.add_middleware(MetricsMiddleware)
app.include_router(metrics_router)

engine: Optional[CapsuleEngine] = None
gui: Optional[AdvancedGUI] = None
_gui_task: Optional[asyncio.Task[None]] = None


@app.on_event("startup")
async def on_startup() -> None:
    """Spin up the CapsuleEngine and attach the Advanced GUI."""

    global engine, gui, _gui_task

    engine = CapsuleEngine()
    await engine.start_background_tasks()

    gui = AdvancedGUI(engine, app)
    if engine.bus is not None:
        _gui_task = asyncio.create_task(gui.run_broadcasters())
        engine.add_background_task(_gui_task)

    log.info("Engine started.")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Tear down the engine and release GUI state."""

    global engine, gui, _gui_task

    if engine is not None:
        await engine.shutdown()

    engine = None
    gui = None
    _gui_task = None


@app.get("/healthz")
async def healthz() -> Dict[str, Any]:
    """Simple health probe endpoint."""

    return {"ok": True}


@app.get("/ready")
async def ready() -> Dict[str, Any]:
    """Readiness probe indicating whether the engine has been initialised."""

    return {"ready": engine is not None}


@app.get("/state/summary")
async def state_summary() -> Dict[str, Any]:
    """Return the CapsuleEngine state summary once the engine is live."""

    if engine is None:
        raise HTTPException(status_code=503, detail="engine not ready")

    return engine.get_state_summary()


@app.post("/ask")
async def ask(q: str) -> Dict[str, Any]:
    """Accept a user question and provide the synthesised LLM context."""

    if engine is None:
        raise HTTPException(status_code=503, detail="engine not ready")

    engine.add_memory("user", q)
    context, system_prompt = engine.belief_state_manager.synthesize_context_for_llm()
    return {"ack": True, "context": context, "system": system_prompt}


@app.post("/graph/edge")
async def add_edge(
    source: str,
    target: str,
    relation: str = "related_to",
) -> Dict[str, Any]:
    """Add an edge to the knowledge graph once the engine is ready."""

    if engine is None:
        raise HTTPException(status_code=503, detail="engine not ready")

    engine.add_graph_edge(source, target, relation)
    graph = {
        "nodes": engine.knowledge_graph.number_of_nodes(),
        "edges": engine.knowledge_graph.number_of_edges(),
    }
    return {"ok": True, "graph": graph}
