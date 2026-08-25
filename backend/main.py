"""
FastAPI backend entry point for AI in Finance project.

This backend handles:
- Chat requests (SLM via Transformers)
- File processing (Text Extraction)
- Analysis & scoring (CSV Generation)
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from contextlib import asynccontextmanager
import logging

# Cap upload size so a single large file can't exhaust memory - there is no
# auth in front of this endpoint. read() is bounded to this many bytes below.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB

# Output token budgets. Plain chat gets a roomier budget than the old 512 so a
# well-structured answer isn't cut off (the persona style guide still caps actual
# length). Web/research/blend answers synthesize over more source material and
# get more still.
CHAT_MAX_TOKENS = 800
WEB_MAX_TOKENS = 1024

# How many prior conversation turns to keep as context (bounds token cost).
MAX_HISTORY_MESSAGES = 8

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

from config.settings import APP_NAME, APP_VERSION
from config.secrets import log_config_summary
from backend.services.file_processor import FileProcessor
from backend.services.scoring_engine import ScoringEngine
from backend.services.llm_service import llm_engine, advice_safety_note
from backend.services.api_providers import LLMProviderError
from backend.services.rag.rag_service import rag_service_manager
from backend.services.metric_extractor import extract_financial_metrics
from backend.services.research_service import (
    web_search,
    iterative_web_search,
    build_web_prompt,
    build_blend_prompt,
    strip_invalid_citations,
)
from backend.services.auth_service import (
    register_user,
    authenticate,
    create_token,
    decode_token,
    AuthError,
)
from backend.services.rate_limiter import API_LIMITER, AUTH_LIMITER, UPLOAD_LIMITER
from backend.db import init_db as db_init_db
from backend.services import history_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# Lifespan Events (Startup/Shutdown)
# -------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load Model
    logger.info("Startup: Loading SLM Model...")
    try:
        # Log which secrets are configured (values are redacted) and warn about
        # any required secret that's missing.
        log_config_summary()
        # Create the database tables (users, chat history) if they don't exist.
        db_init_db()
        # Pre-load the model so the first request isn't slow
        # Warning: This downloads the model if not present (~600MB+)
        llm_engine.load_model()
        # RAG services are created lazily per session_id (see
        # rag_service_manager), so there's nothing shared to pre-warm here.
        # Sweep stale on-disk session dirs so RAG storage stays bounded.
        rag_service_manager.sweep_stale_sessions()
    except Exception as e:
        logger.error(f"Failed to load SLM model on startup: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutdown: Cleaning up resources...")

# -------------------------------------------------
# Create FastAPI app
# -------------------------------------------------
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Backend services for AI in Finance application",
    lifespan=lifespan
)

# -------------------------------------------------
# CORS Middleware
# -------------------------------------------------
# The old config (allow_origins=["*"] together with allow_credentials=True) is
# both unsafe and self-contradictory - browsers reject a wildcard origin when
# credentials are allowed. Default to the local Streamlit origins the frontend
# actually uses, and let a deployment widen this via CORS_ALLOW_ORIGINS
# (comma-separated) without editing code.
import os as _os

_default_origins = "http://localhost:8501,http://127.0.0.1:8501"
_cors_origins = [
    o.strip()
    for o in _os.getenv("CORS_ALLOW_ORIGINS", _default_origins).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Authentication dependency
# -------------------------------------------------
# Every endpoint except "/" (health) and "/auth/*" requires a valid bearer
# token, so the backend is no longer an open API even though it listens on a
# published port. auto_error=False lets us raise our own clean 401 (with a
# WWW-Authenticate header) instead of FastAPI's default 403.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """FastAPI dependency: validate the Authorization: Bearer <token> header and
    return the {'id', 'username'} it encodes. Raises 401 if missing/invalid."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_token(credentials.credentials)
    except AuthError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# -------------------------------------------------
# Rate limiting (abuse control)
# -------------------------------------------------
def _client_ip(request: Request) -> str:
    """Best-effort client IP. Behind the Caddy reverse proxy the real client is
    in X-Forwarded-For (Caddy sets it, and the backend isn't publicly reachable
    except through the proxy — see P0 #4 — so trusting it here is safe)."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _enforce(limiter, key: str) -> None:
    allowed, retry_after = limiter.check(key)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded — please slow down and try again shortly.",
            headers={"Retry-After": str(max(1, int(retry_after) + 1))},
        )


def rate_limit_auth(request: Request) -> None:
    """Per-IP limit for the unauthenticated login/register endpoints."""
    _enforce(AUTH_LIMITER, f"auth:{_client_ip(request)}")


def rate_limited_user(request: Request, user: dict = Depends(get_current_user)) -> dict:
    """Authenticate AND apply the per-user API rate limit. Returns the user so
    endpoints use it in place of get_current_user."""
    _enforce(API_LIMITER, f"user:{user['id']}")
    return user


def rate_limited_upload(request: Request, user: dict = Depends(get_current_user)) -> dict:
    """Per-user API limit plus a stricter per-user upload limit (uploads are
    heavier: extraction + RAG indexing + disk)."""
    _enforce(API_LIMITER, f"user:{user['id']}")
    _enforce(UPLOAD_LIMITER, f"upload:{user['id']}")
    return user


def _scoped_session_id(user: dict, session_id: str) -> str:
    """
    Namespace a client-supplied session id with the authenticated user's id, so
    RAG documents are isolated per user. The user id prefix is server-derived
    (from the verified token), so even if a client sends another user's
    session_id string, the effective storage key still starts with the caller's
    own id and can't collide with — or reach — another user's store.
    """
    raw = (session_id or "default").strip() or "default"
    return f"u{user['id']}-{raw}"


# -------------------------------------------------
# Data Models
# -------------------------------------------------
class AuthRequest(BaseModel):
    username: str
    password: str


class HistorySaveRequest(BaseModel):
    persona: str | None = None
    slm: str | None = None
    messages: list = []


class ChatRequest(BaseModel):
    message: str
    persona: str = "General User"
    slm_model: str = "GPT-OSS 20B (Groq)"
    web_search: bool = False
    # When True (and the session has uploaded documents), the answer blends
    # the user's document context with web results into one cited reply.
    use_documents: bool = False
    session_id: str = "default"
    # Prior conversation turns [{role: "user"|"assistant", content: str}, ...]
    # so answers stay relevant/coherent across a multi-turn chat.
    history: list = []

class AnalysisRequest(BaseModel):
    filename: str
    text_content: str
    model_name: str = "GPT-OSS 20B (Groq)"

class MetricsRequest(BaseModel):
    filename: str = "document"
    text_content: str

class RAGQueryRequest(BaseModel):
    question: str
    session_id: str = "default"
    # Optional persona: when set, the grounded document answer is worded for
    # this reader's finance-knowledge level (the facts/figures never change).
    persona: str = "General User"

class RAGReprocessRequest(BaseModel):
    session_id: str = "default"

# -------------------------------------------------
# Endpoints
# -------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "running",
        "service": "AI in Finance Backend",
        "active_model": llm_engine.current_model_name
    }

# -------------------------------------------------
# Auth endpoints (open — no token required)
# -------------------------------------------------
@app.post("/auth/register")
def register_endpoint(request: AuthRequest, _rl: None = Depends(rate_limit_auth)):
    """Create a new account and return a bearer token so the user is logged in
    immediately after signing up."""
    try:
        user = register_user(request.username, request.password)
        token = create_token(user)
        return {"token": token, "username": user["username"]}
    except AuthError as e:
        # 400 for validation, 409 for a taken username.
        status = 409 if "already taken" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e))


@app.post("/auth/login")
def login_endpoint(request: AuthRequest, _rl: None = Depends(rate_limit_auth)):
    """Verify credentials and return a bearer token."""
    try:
        user = authenticate(request.username, request.password)
        token = create_token(user)
        return {"token": token, "username": user["username"]}
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/auth/me")
def me_endpoint(user: dict = Depends(get_current_user)):
    """Return the current user — used by the frontend to validate a stored
    token on load."""
    return {"id": user["id"], "username": user["username"]}

# -------------------------------------------------
# Chat history (per-user, database-backed)
# -------------------------------------------------
@app.post("/history")
def save_history_endpoint(request: HistorySaveRequest, user: dict = Depends(rate_limited_user)):
    """Save the current conversation to the logged-in user's history."""
    history_id = history_service.save_history(
        user["id"], request.messages, request.persona, request.slm
    )
    return {"id": history_id}


@app.get("/history")
def list_history_endpoint(user: dict = Depends(rate_limited_user)):
    """List the logged-in user's saved chats (metadata only)."""
    return {"histories": history_service.list_histories(user["id"])}


@app.get("/history/{history_id}")
def get_history_endpoint(history_id: int, user: dict = Depends(rate_limited_user)):
    """Load one of the user's saved chats. 404 if it isn't theirs."""
    history = history_service.get_history(user["id"], history_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Chat not found.")
    return history


@app.delete("/history/{history_id}")
def delete_history_endpoint(history_id: int, user: dict = Depends(rate_limited_user)):
    """Delete one of the user's saved chats."""
    deleted = history_service.delete_history(user["id"], history_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found.")
    return {"deleted": True}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, user: dict = Depends(rate_limited_user)):
    """
    Handles chat requests using the selected LLM.

    - web_search: augments the message with live Tavily results (iterative,
      bounded to two searches) and returns the web sources to cite.
    - use_documents (+ web_search): blends the session's uploaded-document
      context with the web results into one cited answer.

    Blocking work (web search, synchronous LLM calls) is run in a threadpool
    so this async endpoint doesn't stall the event loop.
    """
    try:
        logger.info(
            f"Chat Request: {request.message[:20]}... | Persona: {request.persona} "
            f"| web_search={request.web_search} | use_documents={request.use_documents}"
        )

        message = request.message
        sources = []
        web_note = None
        max_tokens = CHAT_MAX_TOKENS

        # Retrieve uploaded-document context (for blending with the web).
        # Scope the session to the authenticated user so document context can
        # only come from this user's own uploads.
        doc_context = ""
        scoped_session = _scoped_session_id(user, request.session_id)
        if request.use_documents and rag_service_manager.session_has_documents(scoped_session):
            rag_service = await rag_service_manager.get(scoped_session)
            doc_context = await rag_service.get_context(request.message)

        # Web search (iterative, bounded) - only if requested.
        web_results = []
        if request.web_search:
            # Fail fast only if NO provider in the fallback chain is usable, so
            # we don't burn a Tavily credit on an unanswerable request.
            llm_engine.ensure_any_provider(request.slm_model)

            def _refine(prompt):
                return llm_engine.generate_response(
                    prompt, persona="General Assistant", model_name=request.slm_model,
                    max_tokens=60,
                )

            web = await run_in_threadpool(iterative_web_search, request.message, _refine)
            if web is None:
                web_note = "Web search is not configured (no TAVILY_API_KEY); answered without web sources."
            elif "error" in web:
                web_note = "Web search failed; answered without web sources."
            elif web.get("results"):
                web_results = web["results"]
            else:
                web_note = "No web results found; answered without web sources."

        # Compose the prompt from whatever context we have.
        if web_results and doc_context:
            message, sources = build_blend_prompt(request.message, doc_context, web_results)
            max_tokens = WEB_MAX_TOKENS
        elif web_results:
            message, sources = build_web_prompt(request.message, web_results)
            max_tokens = WEB_MAX_TOKENS
        elif doc_context:
            # Web unavailable but we have the user's documents: ground in them.
            message = (
                "Answer the user's question using the uploaded document context "
                "below. If it doesn't contain the answer, say so.\n\n"
                f"UPLOADED DOCUMENT CONTEXT:\n{doc_context}\n\n"
                f"QUESTION: {request.message}"
            )
            max_tokens = WEB_MAX_TOKENS

        # Sanitize the client-supplied conversation history: keep only
        # well-formed user/assistant turns, and cap the count to bound tokens.
        history = [
            {"role": m["role"], "content": str(m["content"])}
            for m in (request.history or [])
            if isinstance(m, dict)
            and m.get("role") in ("user", "assistant")
            and m.get("content")
        ][-MAX_HISTORY_MESSAGES:]

        # Synthesize (blocking + per-call fallback) off the event loop.
        response_text, used_model = await run_in_threadpool(
            llm_engine.generate_response_with_model,
            message, request.persona, request.slm_model, max_tokens, history,
        )

        # Drop any [n] citations pointing past the sources we returned.
        if sources:
            response_text = strip_invalid_citations(response_text, len(sources))

        return {
            "response": response_text,
            "model": used_model,
            "sources": sources,
            "web_note": web_note,
        }
    except LLMProviderError as e:
        # Real upstream failure (bad key, rate limit, timeout) - surface as a
        # 502 so the UI shows an error instead of treating it as an answer.
        logger.error(f"LLM provider failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Chat logic failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, user: dict = Depends(rate_limited_user)):
    """
    Streaming variant of /chat for the plain chat path (no web search / no
    document grounding - those need post-processing like citation handling and
    source lists, so they stay on the JSON /chat endpoint). Streams the answer
    as text/plain chunks so the UI can render tokens as they arrive instead of
    waiting for the whole response.

    Errors are yielded as text inside the stream (rather than raised) because
    the HTTP 200 + headers are already committed once streaming begins.
    """
    # Same history sanitation as /chat.
    history = [
        {"role": m["role"], "content": str(m["content"])}
        for m in (request.history or [])
        if isinstance(m, dict)
        and m.get("role") in ("user", "assistant")
        and m.get("content")
    ][-MAX_HISTORY_MESSAGES:]

    def _generate():
        collected = []
        try:
            for piece in llm_engine.stream_response_with_model(
                request.message, request.persona, request.slm_model,
                CHAT_MAX_TOKENS, history,
            ):
                collected.append(piece)
                yield piece
            # Backstop: if a personal-advice question got flattened to a bare
            # yes/no, append the required educational framing after the stream.
            note = advice_safety_note(request.message, "".join(collected))
            if note:
                yield f"\n\n{note}"
        except LLMProviderError as e:
            logger.error(f"Chat stream provider failure: {e}")
            yield f"\n\n⚠️ The model could not answer: {e}"
        except Exception as e:
            logger.error(f"Chat stream failed: {e}")
            yield f"\n\n⚠️ Unexpected error: {e}"

    return StreamingResponse(_generate(), media_type="text/plain; charset=utf-8")


@app.post("/files")
async def file_processing_endpoint(
    file: UploadFile = File(...),
    session_id: str = Form("default"),
    user: dict = Depends(rate_limited_upload),
):
    """
    Receives an uploaded file, determines type, and extracts text.
    RAG indexing is scoped to the caller's session_id so uploaded
    documents aren't visible to other sessions.
    """
    try:
        # Read at most MAX_UPLOAD_BYTES+1 so an oversized upload can't OOM the
        # backend; read(size) bounds how much is pulled into memory.
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit.",
            )

        # Text extraction (pdfplumber parsing, OCR) is synchronous and
        # CPU-heavy; run it in a threadpool so a large or scanned PDF doesn't
        # block the event loop and freeze chat/RAG for every other request.
        text = await run_in_threadpool(FileProcessor.extract_text, content, file.filename)

        # Couldn't usefully read the file - a scanned/image PDF that OCR
        # couldn't handle, or a genuinely empty file. (Short but real text/
        # CSV/Word uploads are NOT rejected - see extraction_insufficient.)
        if FileProcessor.extraction_insufficient(text, file.filename):
            warning = (
                "No readable text could be extracted from this file. It may be "
                "empty, or a scanned/image-based document that needs OCR. It has "
                "not been indexed for document Q&A."
            )
            logger.warning(f"Low-quality extraction for {file.filename}: {len(text.strip())} chars")
            return {
                "filename": file.filename,
                "message": warning,
                "rag_indexed": False,
                "extraction_warning": warning,
                "extracted_text_preview": text[:200],
                "full_text": text,
            }

        rag_service = await rag_service_manager.get(_scoped_session_id(user, session_id))
        rag_result = await rag_service.ingest_document(text, file_path=file.filename)

        if rag_result["indexed"]:
            if rag_result.get("duplicate"):
                message = "This document's content is already indexed in your session and is searchable."
            elif rag_result.get("replaced"):
                message = "File processed successfully (replaced the previous version of this file)."
            else:
                message = "File processed successfully"
        else:
            error_text = rag_result["error"] or ""
            is_rate_limit = "rate_limit" in error_text.lower() or "429" in error_text

            if is_rate_limit:
                message = (
                    "Text extracted successfully, but RAG indexing hit the Groq "
                    "rate limit and couldn't finish. This document isn't searchable "
                    "yet - wait a minute for the limit to reset, then use "
                    "'🔄 Retry failed document indexing' below."
                )
            else:
                message = (
                    "Text extracted successfully, but RAG indexing failed: "
                    f"{error_text}. This document won't be searchable "
                    "via 'Answer using my uploaded documents'."
                )

            logger.warning(f"RAG indexing failed for {file.filename}: {error_text}")

        return {
            "filename": file.filename,
            "message": message,
            "rag_indexed": rag_result["indexed"],
            "extracted_text_preview": text[:200],
            "full_text": text
        }
    except HTTPException:
        # Deliberate responses (e.g. 413 too-large) must pass through, not be
        # rewritten into a generic 400 below.
        raise
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/metrics")
async def metrics_endpoint(request: MetricsRequest, user: dict = Depends(rate_limited_user)):
    """
    Extracts explicitly-stated financial metrics (revenue, profit, margins,
    ratios, etc.) from a document's extracted text as structured rows.
    """
    try:
        result = await extract_financial_metrics(request.text_content)
        return result
    except Exception as e:
        logger.error(f"Metric extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/ask")
async def rag_ask_endpoint(request: RAGQueryRequest, user: dict = Depends(rate_limited_user)):
    """
    Answers a question grounded in documents uploaded during this session
    only (see session_id) - not the global set of every uploaded document.
    """
    try:
        # No documents yet: answer directly, and don't initialize a store
        # (which would leave an empty session directory on disk).
        scoped_session = _scoped_session_id(user, request.session_id)
        if not rag_service_manager.session_has_documents(scoped_session):
            return {
                "answer": "You haven't uploaded any documents in this session yet. "
                          "Upload a document first, then ask about it."
            }

        rag_service = await rag_service_manager.get(scoped_session)
        answer = await rag_service.ask(request.question, persona=request.persona)

        # Replace LightRAG's internal "[no-context]" sentinel with a clean
        # message so the raw marker never reaches the user.
        if answer and "[no-context]" in answer.lower():
            answer = ("I couldn't find anything relevant to that question in your "
                      "uploaded documents.")

        return {"answer": answer}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/reprocess")
async def rag_reprocess_endpoint(request: RAGReprocessRequest, user: dict = Depends(rate_limited_user)):
    """
    Retries any documents in this session whose RAG indexing previously
    failed (e.g. a provider rate limit mid-extraction), so they can gain
    full graph-based retrieval instead of staying vector-only forever.
    """
    try:
        rag_service = await rag_service_manager.get(_scoped_session_id(user, request.session_id))
        result = await rag_service.reprocess_failed_documents()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"RAG reprocess failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analysis")
def analysis_endpoint(request: AnalysisRequest, user: dict = Depends(rate_limited_user)):
    """
    Triggers the scoring engine to generate analysis CSV.
    """
    try:
        csv_file = ScoringEngine.analyze_and_score(
            request.filename,
            request.text_content,
            request.model_name
        )
        return {
            "message": "Analysis complete",
            "csv_file": csv_file
        }
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))