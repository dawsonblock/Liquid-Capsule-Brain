"""FastAPI application wiring for the Capsule Brain service."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from capsule_brain.core.capsule_engine import CapsuleEngine
from capsule_brain.gui.gui import AdvancedGUI
from capsule_brain.observability import metrics as metrics_module


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage the CapsuleEngine and GUI lifecycle for the FastAPI app."""

    engine = CapsuleEngine()
    await engine.start_background_tasks()
    app.state.engine = engine

    gui = AdvancedGUI(engine, app)
    app.state.gui = gui

    if engine.bus is not None:
        engine.add_background_task(
            asyncio.create_task(
                gui.run_broadcasters(),
                name="capsule-brain-gui-broadcaster",
            )
        )

    try:
        yield
    finally:
        if getattr(app.state, "gui", None) is not None:
            await gui.close()
            app.state.gui = None

        if getattr(app.state, "engine", None) is not None:
            await engine.shutdown()
            app.state.engine = None


app = FastAPI(title="Capsule Brain Supreme AGI", version="1.0.1", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics
app.add_middleware(cast(Any, metrics_module.MetricsMiddleware))
app.include_router(metrics_module.router)

def _get_engine_or_503() -> CapsuleEngine:
    engine = getattr(app.state, "engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="engine not ready")
    return cast(CapsuleEngine, engine)


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    """Simple health probe endpoint."""

    return {"ok": True}


@app.get("/ready")
async def ready() -> dict[str, Any]:
    """Readiness probe indicating whether the engine has been initialised."""

    return {"ready": getattr(app.state, "engine", None) is not None}


@app.get("/state/summary")
async def state_summary() -> dict[str, Any]:
    """Return the CapsuleEngine state summary once the engine is live."""

    engine = _get_engine_or_503()
    return engine.get_state_summary()


@app.post("/ask")
async def ask(q: str) -> dict[str, Any]:
    """Accept a user question and provide the synthesised LLM context."""

    engine = _get_engine_or_503()

    engine.add_memory("user", q)
    context, system_prompt = engine.belief_state_manager.synthesize_context_for_llm()
    return {"ack": True, "context": context, "system": system_prompt}


@app.post("/graph/edge")
async def add_edge(
    source: str,
    target: str,
    relation: str = "related_to",
) -> dict[str, Any]:
    """Add an edge to the knowledge graph once the engine is ready."""

    engine = _get_engine_or_503()

    engine.add_graph_edge(source, target, relation)
    graph = {
        "nodes": engine.knowledge_graph.number_of_nodes(),
        "edges": engine.knowledge_graph.number_of_edges(),
    }
    return {"ok": True, "graph": graph}
