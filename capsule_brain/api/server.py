import logging
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from capsule_brain.core.capsule_engine import CapsuleEngine
from capsule_brain.observability.metrics import MetricsMiddleware
from capsule_brain.observability.metrics import router as metrics_router
from capsule_brain.security.admin import require_admin_token

log = logging.getLogger(__name__)
app = FastAPI(title="Capsule Brain Supreme AGI", version="1.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(MetricsMiddleware)
app.include_router(metrics_router)

engine: CapsuleEngine | None = None


@app.on_event("startup")
async def on_startup() -> None:
    global engine
    engine = CapsuleEngine()
    await engine.start_background_tasks(app)
    log.info("Engine started.")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global engine
    if engine:
        await engine.shutdown()
        engine = None


@app.get("/healthz", dependencies=[Depends(require_admin_token)])
async def healthz() -> dict[str, Any]:
    return {"ok": True}


@app.get("/ready", dependencies=[Depends(require_admin_token)])
async def ready() -> dict[str, Any]:
    return {"ready": engine is not None}


@app.get("/state/summary", dependencies=[Depends(require_admin_token)])
async def state_summary() -> dict[str, Any]:
    if not engine:
        raise HTTPException(status_code=503, detail="engine not ready")
    return engine.get_state_summary()


@app.post("/ask")
async def ask(q: str) -> dict[str, Any]:
    if not engine:
        raise HTTPException(status_code=503, detail="engine not ready")

    engine.add_memory("user", q)
    context, system_prompt = engine.belief_state_manager.synthesize_context_for_llm()
    return {"ack": True, "context": context, "system": system_prompt}


@app.post("/graph/edge", dependencies=[Depends(require_admin_token)])
async def add_edge(
    source: str, target: str, relation: str = "related_to"
) -> dict[str, Any]:
    if not engine:
        raise HTTPException(status_code=503, detail="engine not ready")

    engine.add_graph_edge(source, target, relation)
    return {
        "ok": True,
        "graph": {
            "nodes": engine.knowledge_graph.number_of_nodes(),
            "edges": engine.knowledge_graph.number_of_edges(),
        },
    }
