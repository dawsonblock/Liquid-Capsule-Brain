import asyncio
import logging
import os
import time
from collections.abc import AsyncIterator, Awaitable, Callable
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
from fastapi.responses import Response
from pydantic import BaseModel

from capsule_brain.api.dependencies import (
    attach_engine,
    detach_engine,
    get_engine,
    peek_engine,
)
from capsule_brain.core.capsule_engine import CapsuleEngine
from capsule_brain.gui.gui import AdvancedGUI
from capsule_brain.ingestion.extractor import extract_bytes
from capsule_brain.observability.metrics import (
    record_llm_tokens,
    record_ask_request,
    record_ask_duration,
    record_file_upload,
    setup_metrics,
)
from capsule_brain.observability.tracing import setup_tracing
from capsule_brain.security.admin import require_admin_token
from capsule_brain.security.headers import SecurityHeadersMiddleware
from capsule_brain.security.rate_limiter import check_rate_limit
from capsule_brain.debugging.advanced_debugger import advanced_debugger
from capsule_brain.debugging.logging_config import LoggingMiddleware, setup_advanced_logging
from capsule_brain.debugging.memory_debugger import memory_debugger
from capsule_brain.debugging.profiler import advanced_profiler
from capsule_brain.debugging.static_analysis import static_analyzer
from capsule_brain.enhancements.performance_optimizer import performance_optimizer
from capsule_brain.enhancements.security_enhancer import security_enhancer
from capsule_brain.enhancements.monitoring_dashboard import monitoring_dashboard

log = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(fastapi_app: FastAPI) -> AsyncIterator[None]:
    # Initialize advanced debugging systems
    setup_advanced_logging()
    memory_debugger.take_snapshot("app_startup")
    
    capsule_engine = CapsuleEngine()
    attach_engine(fastapi_app, capsule_engine)
    await capsule_engine.start_background_tasks(fastapi_app)
    gui = AdvancedGUI(capsule_engine, fastapi_app)
    fastapi_app.state.gui = gui
    broadcaster_task = asyncio.create_task(fastapi_app.state.gui.run_broadcasters())
    
    # Take memory snapshot after initialization
    memory_debugger.take_snapshot("app_initialized")
    
    # Start monitoring dashboard
    await monitoring_dashboard.start_collection()
    
    log.info("Engine started with advanced debugging and enhancements enabled.")
    try:
        yield
    finally:
        # Take final memory snapshot
        memory_debugger.take_snapshot("app_shutdown")
        
        # Stop monitoring dashboard
        await monitoring_dashboard.stop_collection()
        
        broadcaster_task.cancel()
        try:
            await broadcaster_task
        except asyncio.CancelledError:
            pass
        attached = detach_engine(fastapi_app)
        if attached:
            await attached.shutdown()


app = FastAPI(
    title="Capsule Brain Supreme AGI",
    version="1.0.1",
    lifespan=app_lifespan,
)

# Configure CORS from environment
_cors = os.getenv("CORS_ORIGINS") or os.getenv("ALLOW_ORIGINS", "*")
origins = ["*"] if _cors == "*" else [o.strip() for o in _cors.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add advanced logging middleware
app.add_middleware(LoggingMiddleware)


# Add cache control headers for static files
@app.middleware("http")
async def add_cache_control_header(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    if request.url.path.endswith((".js", ".css")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# Configure Prometheus metrics before app startup
setup_metrics(app)
setup_tracing(app)

EngineDep = Annotated[CapsuleEngine, Depends(get_engine)]


class AskRequest(BaseModel):
    q: str


@app.get("/healthz", dependencies=[Depends(require_admin_token)])
async def healthz(request: Request) -> dict[str, Any]:
    check_rate_limit(request)
    return {"ok": True}


@app.get("/ready", dependencies=[Depends(require_admin_token)])
async def ready(request: Request) -> dict[str, Any]:
    check_rate_limit(request)
    return {"ready": peek_engine(request.app) is not None}


@app.get("/state/summary", dependencies=[Depends(require_admin_token)])
async def state_summary(request: Request, engine: EngineDep) -> dict[str, Any]:
    check_rate_limit(request)
    return engine.get_state_summary()


@app.post("/ask")
@advanced_debugger.debug_function
@advanced_profiler.profile_decorator
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
    except (ValueError, TypeError, KeyError):  # defensive metrics guard
        pass

    context, system_prompt = engine.belief_state_manager.synthesize_context_for_llm()
    return {
        "ack": True,
        "context": context,
        "system": system_prompt,
        "llm_response": llm_response,
    }


@app.post("/ask_with_document")
@performance_optimizer.cache_decorator(ttl=300)  # Cache for 5 minutes
async def ask_with_document(
    engine: EngineDep,
    file: UploadFile = File(...),  # noqa: B008
    q: str = Form("Document question"),
) -> dict[str, Any]:
    q_value = q or "Document question"

    try:
        # Read the uploaded file content
        file_content = await file.read()

        # Enforce upload size limit
        MAX_BYTES = int(os.getenv("UPLOAD_MAX_BYTES", "10485760"))  # 10 MiB
        if len(file_content) > MAX_BYTES:
            raise HTTPException(
                status_code=413, detail=f"File too large. Maximum size: {MAX_BYTES} bytes"
            )
        
        # Validate content type
        ALLOWED_CONTENT_TYPES = {
            "application/pdf",
            "text/plain",
            "text/markdown",
            "application/zip",
            "text/csv",
            "application/json",
        }
        
        if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=415, 
                detail=f"Unsupported file type: {file.content_type}. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
            )
        
        log.info("Processing uploaded file: %s (%d bytes, %s)", file.filename, len(file_content), file.content_type)

        # Extract text content from the file
        extracted_text, file_meta = extract_bytes(
            file.filename or "unknown", file.content_type, file_content
        )

        log.info("Extracted text length: %d characters", len(extracted_text))
        log.info("File metadata: %s", file_meta)

        # Create a comprehensive query with the document content
        document_query = f"""
Question: {q_value}

Document: {file.filename}
File Type: {file_meta.get('type', 'unknown')}
File Size: {file_meta.get('bytes', 0)} bytes

Document Content:
{extracted_text[:8000]}  # Limit to first 8000 chars to avoid token limits
"""

        # Add to memory with extracted content
        engine.add_memory("user", document_query)
        engine.belief_state_manager.current_query = q_value

        # Update belief state with document context
        engine.belief_state_manager.retrieved_knowledge = [
            f"Document: {file.filename} ({file_meta.get('type', 'unknown')})",
            f"Content preview: {extracted_text[:200]}...",
        ]

        # Generate LLM response
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
        except (ValueError, TypeError, KeyError):
            pass

        context, system_prompt = engine.belief_state_manager.synthesize_context_for_llm()

        return {
            "ack": True,
            "context": context,
            "system": system_prompt,
            "llm_response": llm_response,
            "file_processed": {
                "filename": file.filename,
                "type": file_meta.get("type"),
                "size": file_meta.get("bytes"),
                "extracted_length": len(extracted_text),
                "preview": (
                    extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
                ),
            },
        }

    except (OSError, ValueError, TypeError, KeyError) as e:
        log.error("Error processing uploaded file: %s", e)
        # Fallback: just record the filename without content
        engine.add_memory(
            "user", f"{q_value}\n[Attached file: {file.filename} " f"- processing failed: {str(e)}]"
        )
        engine.belief_state_manager.current_query = q_value

        llm_response = await engine.belief_state_manager.generate_llm_response()
        if llm_response.get("text"):
            engine.add_memory("assistant", llm_response["text"])

        return {
            "ack": True,
            "error": f"File processing failed: {str(e)}",
            "llm_response": llm_response,
        }


@app.get("/debug/env")
async def debug_env(request: Request) -> dict[str, Any]:
    """Debug endpoint to check environment variables."""
    # Only allow in development environments or with admin token
    env = os.getenv("APP_ENV", "development").lower()
    if env not in {"local", "development", "dev"}:
        # Check for admin token in production
        from capsule_brain.security.admin import require_admin_token

        try:
            require_admin_token(request.headers.get("x-admin-token"))
        except Exception:
            raise HTTPException(status_code=404, detail="Not found") from None
    admin_val = os.getenv("ADMIN_TOKEN")
    return {
        "admin_token_set": bool(admin_val),
        "admin_token_value": ((admin_val[:10] + "...") if admin_val else "NOT_SET"),
        "deepseek_key_set": bool(os.getenv("DEEPSEEK_API_KEY")),
        "app_env": os.getenv("APP_ENV", "NOT_SET"),
        "app_profile": os.getenv("APP_PROFILE", "NOT_SET"),
    }


@app.get("/debug/summary", dependencies=[Depends(require_admin_token)])
async def debug_summary() -> dict[str, Any]:
    """Get comprehensive debugging summary."""
    return {
        "advanced_debugger": advanced_debugger.get_debug_summary(),
        "memory_debugger": memory_debugger.get_memory_summary(),
        "profiler": advanced_profiler.get_profile_summary(),
        "static_analyzer": static_analyzer.get_analysis_summary(),
    }


@app.get("/debug/memory", dependencies=[Depends(require_admin_token)])
async def debug_memory() -> dict[str, Any]:
    """Get memory debugging information."""
    return memory_debugger.get_memory_summary()


@app.get("/debug/performance", dependencies=[Depends(require_admin_token)])
async def debug_performance() -> dict[str, Any]:
    """Get performance profiling information."""
    return advanced_profiler.get_detailed_profile_report()


@app.get("/debug/analysis", dependencies=[Depends(require_admin_token)])
async def debug_analysis() -> dict[str, Any]:
    """Get static analysis results."""
    return static_analyzer.get_detailed_report()


@app.post("/debug/gc", dependencies=[Depends(require_admin_token)])
async def debug_garbage_collection() -> dict[str, Any]:
    """Force garbage collection and return statistics."""
    return memory_debugger.force_garbage_collection()


@app.post("/debug/snapshot", dependencies=[Depends(require_admin_token)])
async def debug_snapshot(label: str = "manual") -> dict[str, Any]:
    """Take a memory snapshot."""
    snapshot = memory_debugger.take_snapshot(label)
    if snapshot is None:
        return {
            "snapshot_taken": False,
            "debug_enabled": False,
            "label": label,
            "message": "Memory debugging is disabled"
        }
    return {
        "snapshot_taken": True,
        "label": label,
        "timestamp": snapshot.timestamp,
        "memory_usage_mb": snapshot.memory_usage / 1024 / 1024,
        "objects_count": snapshot.objects_count,
    }


@app.get("/enhancements/summary", dependencies=[Depends(require_admin_token)])
async def enhancements_summary() -> dict[str, Any]:
    """Get comprehensive enhancements summary."""
    return {
        "performance_optimizer": performance_optimizer.get_performance_summary(),
        "security_enhancer": security_enhancer.get_security_summary(),
        "monitoring_dashboard": monitoring_dashboard.get_dashboard_data(),
    }


@app.get("/enhancements/performance", dependencies=[Depends(require_admin_token)])
async def enhancements_performance() -> dict[str, Any]:
    """Get performance optimization information."""
    return performance_optimizer.get_performance_summary()


@app.get("/enhancements/security", dependencies=[Depends(require_admin_token)])
async def enhancements_security() -> dict[str, Any]:
    """Get security enhancement information."""
    return security_enhancer.get_security_summary()


@app.get("/enhancements/monitoring", dependencies=[Depends(require_admin_token)])
async def enhancements_monitoring() -> dict[str, Any]:
    """Get monitoring dashboard information."""
    return monitoring_dashboard.get_dashboard_data()


@app.get("/enhancements/health", dependencies=[Depends(require_admin_token)])
async def enhancements_health() -> dict[str, Any]:
    """Get overall system health status."""
    return monitoring_dashboard.get_health_status()


@app.post("/enhancements/optimize-cache", dependencies=[Depends(require_admin_token)])
async def optimize_cache() -> dict[str, Any]:
    """Optimize cache performance."""
    return performance_optimizer.optimize_cache()


@app.post("/enhancements/analyze-security", dependencies=[Depends(require_admin_token)])
async def analyze_security(request: Request) -> dict[str, Any]:
    """Analyze request for security threats."""
    request_data = {
        "path": request.url.path,
        "query_string": str(request.query_params),
        "method": request.method,
        "source_ip": request.client.host if request.client else "unknown",
        "headers": dict(request.headers)
    }
    return security_enhancer.analyze_request(request_data)


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
    log.info("Overseer enable request received")
    engine.enable_overseer()
    if not engine.overseer:
        await engine.start_overseer()
    log.info("Overseer enabled successfully")
    return {"ok": True, "overseer_enabled": engine.overseer_enabled}


@app.post("/overseer/disable", dependencies=[Depends(require_admin_token)])
async def disable_overseer(engine: EngineDep) -> dict[str, Any]:
    """Disable the AI overseer."""
    log.info("Overseer disable request received")
    engine.disable_overseer()
    await engine.stop_overseer()
    log.info("Overseer disabled successfully")
    return {"ok": True, "overseer_enabled": engine.overseer_enabled}


@app.get("/overseer/status")
async def overseer_status(engine: EngineDep) -> dict[str, Any]:
    """Get the current status of the AI overseer."""
    return {
        "overseer_enabled": engine.overseer_enabled,
        "overseer_running": engine.overseer is not None,
    }


class OracleRequest(BaseModel):
    action: str


@app.post("/oracle", dependencies=[Depends(require_admin_token)])
async def oracle_control(request: OracleRequest, engine: EngineDep) -> dict[str, Any]:
    """Oracle control endpoint for external system integration."""
    action = request.action.lower()

    if action == "on":
        # Enable all systems
        engine.enable_overseer()
        if not engine.overseer:
            await engine.start_overseer()
        return {
            "ok": True,
            "action": "on",
            "message": "Oracle enabled - all systems active",
            "overseer_enabled": engine.overseer_enabled,
            "timestamp": time.time(),
        }
    elif action == "off":
        # Disable all systems
        engine.disable_overseer()
        await engine.stop_overseer()
        return {
            "ok": True,
            "action": "off",
            "message": "Oracle disabled - systems in standby",
            "overseer_enabled": engine.overseer_enabled,
            "timestamp": time.time(),
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'on' or 'off'")
