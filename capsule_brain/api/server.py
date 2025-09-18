import logging
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from capsule_brain.api.dependencies import (
    attach_engine,
    detach_engine,
    get_engine,
    peek_engine,
)
from capsule_brain.core.capsule_engine import CapsuleEngine
from capsule_brain.observability.metrics import setup_metrics
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
setup_metrics(app)

EngineDep = Annotated[CapsuleEngine, Depends(get_engine)]


@app.on_event("startup")
async def on_startup() -> None:
    capsule_engine = CapsuleEngine()
    attach_engine(app, capsule_engine)
    await capsule_engine.start_background_tasks(app)
    log.info("Engine started.")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    attached = detach_engine(app)
    if attached:
        await attached.shutdown()


@app.get("/healthz", dependencies=[Depends(require_admin_token)])
async def healthz() -> dict[str, Any]:
    return {"ok": True}


@app.get("/ready", dependencies=[Depends(require_admin_token)])
async def ready(request: Request) -> dict[str, Any]:
    return {"ready": peek_engine(request.app) is not None}


@app.get("/state/summary", dependencies=[Depends(require_admin_token)])
async def state_summary(engine: EngineDep) -> dict[str, Any]:
    return engine.get_state_summary()


@app.post("/ask")
async def ask(q: str, engine: EngineDep) -> dict[str, Any]:
    engine.add_memory("user", q)
    engine.belief_state_manager.current_query = q
    
    # Generate LLM response using DeepSeek
    llm_response = await engine.belief_state_manager.generate_llm_response()
    
    # Add the response to memory
    if llm_response.get("text"):
        engine.add_memory("assistant", llm_response["text"])
    
    context, system_prompt = engine.belief_state_manager.synthesize_context_for_llm()
    return {
        "ack": True, 
        "context": context, 
        "system": system_prompt,
        "llm_response": llm_response
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
