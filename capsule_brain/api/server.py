import asyncio, logging, os
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from capsule_brain.core.capsule_engine import CapsuleEngine
from capsule_brain.observability.metrics import router as metrics_router, MetricsMiddleware

log = logging.getLogger(__name__)
app = FastAPI(title="Capsule Brain Supreme AGI", version="1.0.1")

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
# Metrics
app.add_middleware(MetricsMiddleware)
app.include_router(metrics_router)

engine: CapsuleEngine | None = None


class AskPayload(BaseModel):
    q: str

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
async def healthz() -> Dict[str, Any]:
    return {"ok": True}

@app.get("/ready")
async def ready() -> Dict[str, Any]:
    return {"ready": engine is not None}

@app.get("/state/summary")
async def state_summary() -> Dict[str, Any]:
    if not engine: raise HTTPException(status_code=503, detail="engine not ready")
    return engine.get_state_summary()

@app.post("/ask")
async def ask(payload: AskPayload) -> Dict[str, Any]:
    if not engine:
        raise HTTPException(status_code=503, detail="engine not ready")

    question = payload.q
    engine.add_memory("user", question)
    context, system_prompt = engine.belief_state_manager.synthesize_context_for_llm()
    return {"ack": True, "question": question, "context": context, "system": system_prompt}


@app.post("/ask_with_document")
async def ask_with_document(
    file: Optional[UploadFile] = File(None),
    question: Optional[str] = Form(None),
) -> Dict[str, Any]:
    if not engine:
        raise HTTPException(status_code=503, detail="engine not ready")

    if file is None:
        raise HTTPException(status_code=400, detail="file is required")

    contents = await file.read()
    size = len(contents) if contents is not None else 0
    metadata = {
        "filename": file.filename,
        "content_type": file.content_type or "application/octet-stream",
        "size": size,
    }

    engine.add_memory(
        "attachment",
        f"Received file '{metadata['filename']}' ({metadata['content_type']}, {metadata['size']} bytes)",
    )

    if question:
        engine.add_memory("user", question)

    context, system_prompt = engine.belief_state_manager.synthesize_context_for_llm()
    return {
        "ack": True,
        "question": question,
        "document": metadata,
        "context": context,
        "system": system_prompt,
    }

@app.post("/graph/edge")
async def add_edge(source: str, target: str, relation: str = "related_to") -> Dict[str, Any]:
    if not engine: raise HTTPException(status_code=503, detail="engine not ready")
    engine.add_graph_edge(source, target, relation)
    return {"ok": True, "graph": {"nodes": engine.knowledge_graph.number_of_nodes(), "edges": engine.knowledge_graph.number_of_edges()}}
