import logging
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from capsule_brain.core.capsule_engine import CapsuleEngine
from capsule_brain.observability.metrics import MetricsMiddleware
from capsule_brain.observability.metrics import router as metrics_router

log = logging.getLogger(__name__)
app = FastAPI(title="Capsule Brain Supreme AGI", version="1.0.1")

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
# Metrics
app.add_middleware(MetricsMiddleware)
app.include_router(metrics_router)

engine: CapsuleEngine | None = None
ASK_REQUEST_BODY = Body(default=None)
ASK_QUERY_PARAM = Query(default=None)


class AskRequest(BaseModel):
    """Payload accepted by the /ask endpoint."""

    question: str | None = Field(default=None, alias="q")

    model_config = ConfigDict(populate_by_name=True)

    def extract(self) -> str | None:
        """Return the provided question regardless of the key used."""

        return self.question

@app.on_event("startup")
async def on_startup() -> None:
    global engine
    engine = CapsuleEngine()
    await engine.start_background_tasks()
    log.info("Engine started.")

@app.on_event("shutdown")
async def on_shutdown() -> None:
    if engine:
        await engine.shutdown()

@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {"ok": True}

@app.get("/ready")
async def ready() -> dict[str, Any]:
    return {"ready": engine is not None}

@app.get("/state/summary")
async def state_summary() -> dict[str, Any]:
    if not engine:
        raise HTTPException(status_code=503, detail="engine not ready")
    assert engine is not None
    return engine.get_state_summary()

@app.post("/ask")
async def ask(
    ask_request: AskRequest | None = ASK_REQUEST_BODY,
    q: str | None = ASK_QUERY_PARAM,
) -> dict[str, Any]:
    if not engine:
        raise HTTPException(status_code=503, detail="engine not ready")
    assert engine is not None
    current_engine = engine
    question = ask_request.extract() if ask_request else None
    if question is None:
        question = q
    if question is None:
        raise HTTPException(status_code=422, detail="q is required")
    current_engine.add_memory("user", question)
    context, system_prompt = current_engine.belief_state_manager.synthesize_context_for_llm()
    return {"ack": True, "context": context, "system": system_prompt}

@app.post("/graph/edge")
async def add_edge(source: str, target: str, relation: str = "related_to") -> dict[str, Any]:
    if not engine:
        raise HTTPException(status_code=503, detail="engine not ready")
    assert engine is not None
    engine.add_graph_edge(source, target, relation)
    return {
        "ok": True,
        "graph": {
            "nodes": engine.knowledge_graph.number_of_nodes(),
            "edges": engine.knowledge_graph.number_of_edges(),
        },
    }
