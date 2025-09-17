import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import AliasChoices, BaseModel, Field, ValidationError

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
ASK_QUERY_PARAM = Query(default=None)


class AskRequest(BaseModel):
    """Payload accepted by the /ask endpoint."""

    question: str | None = Field(
        default=None, validation_alias=AliasChoices("question", "q")
    )

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
async def ask(request: Request, q: str | None = ASK_QUERY_PARAM) -> dict[str, Any]:
    if not engine:
        raise HTTPException(status_code=503, detail="engine not ready")
    assert engine is not None
    current_engine = engine
    question: str | None = None
    if question is None:
        try:
            raw_payload = await request.json()
        except ValueError:
            raw_payload = None
        if isinstance(raw_payload, dict):
            try:
                question = AskRequest.model_validate(raw_payload).question
            except ValidationError:
                question = None
        elif isinstance(raw_payload, str):
            question = raw_payload
    if question is None:
        try:
            form = await request.form()
        except Exception:  # pragma: no cover - defensive guard
            form = None
        if form is not None:
            form_q = form.get("q") or form.get("question")
            if isinstance(form_q, str):
                question = form_q
    if question is None:
        content_type = request.headers.get("content-type", "")
        if "text/plain" in content_type or not content_type:
            body_bytes = await request.body()
            if body_bytes:
                candidate = body_bytes.decode("utf-8", errors="ignore").strip()
                if candidate:
                    question = candidate
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
