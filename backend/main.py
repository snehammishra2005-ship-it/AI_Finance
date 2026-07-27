"""
FastAPI backend entry point for AI in Finance project.

This backend handles:
- Chat requests (SLM via Transformers)
- File processing (Text Extraction)
- Analysis & scoring (CSV Generation)
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import logging

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

from config.settings import APP_NAME, APP_VERSION
from backend.services.file_processor import FileProcessor
from backend.services.scoring_engine import ScoringEngine
from backend.services.llm_service import llm_engine
from backend.services.api_providers import LLMProviderError
from backend.services.rag.rag_service import rag_service_manager
from backend.services.metric_extractor import extract_financial_metrics
from backend.services.research_service import web_search, build_web_prompt

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Data Models
# -------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    persona: str = "General User"
    slm_model: str = "Llama 3.1 8B Instant (Groq)"
    web_search: bool = False

class AnalysisRequest(BaseModel):
    filename: str
    text_content: str
    model_name: str = "Llama 3.1 8B Instant (Groq)"

class MetricsRequest(BaseModel):
    filename: str = "document"
    text_content: str

class RAGQueryRequest(BaseModel):
    question: str
    session_id: str = "default"

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

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    """
    Handles chat requests using the selected LLM. When web_search is enabled,
    the message is augmented with live Tavily results and the response is
    returned alongside the list of web sources the model was given to cite.
    """
    try:
        logger.info(
            f"Chat Request: {request.message[:20]}... | Persona: {request.persona} "
            f"| web_search={request.web_search}"
        )

        llm_engine.load_model(request.slm_model)

        message = request.message
        sources = []
        web_note = None

        if request.web_search:
            web = web_search(request.message)
            if web is None:
                web_note = "Web search is not configured (no TAVILY_API_KEY); answered without web sources."
            elif "error" in web:
                web_note = "Web search failed; answered without web sources."
            elif web.get("results"):
                message, sources = build_web_prompt(request.message, web["results"])
            else:
                web_note = "No web results found; answered without web sources."

        response_text = llm_engine.generate_response(
            message=message,
            persona=request.persona
        )

        return {
            "response": response_text,
            "model": request.slm_model,
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

@app.post("/files")
async def file_processing_endpoint(
    file: UploadFile = File(...),
    session_id: str = Form("default")
):
    """
    Receives an uploaded file, determines type, and extracts text.
    RAG indexing is scoped to the caller's session_id so uploaded
    documents aren't visible to other sessions.
    """
    try:
        content = await file.read()
        text = FileProcessor.extract_text(content, file.filename)

        # Almost no text came out - likely a scanned/image PDF with no OCR
        # available, or an empty/unreadable file. Warn instead of silently
        # indexing near-nothing.
        if FileProcessor.looks_empty(text):
            warning = (
                "Very little readable text could be extracted from this file. "
                "It may be a scanned or image-based document (which needs OCR), "
                "or it may be empty. It has not been indexed for document Q&A."
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

        rag_service = await rag_service_manager.get(session_id)
        rag_result = await rag_service.ingest_document(text, file_path=file.filename)

        if rag_result["indexed"]:
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
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/metrics")
async def metrics_endpoint(request: MetricsRequest):
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
async def rag_ask_endpoint(request: RAGQueryRequest):
    """
    Answers a question grounded in documents uploaded during this session
    only (see session_id) - not the global set of every uploaded document.
    """
    try:
        rag_service = await rag_service_manager.get(request.session_id)
        answer = await rag_service.ask(request.question)
        return {"answer": answer}
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/reprocess")
async def rag_reprocess_endpoint(request: RAGReprocessRequest):
    """
    Retries any documents in this session whose RAG indexing previously
    failed (e.g. a provider rate limit mid-extraction), so they can gain
    full graph-based retrieval instead of staying vector-only forever.
    """
    try:
        rag_service = await rag_service_manager.get(request.session_id)
        result = await rag_service.reprocess_failed_documents()
        return result
    except Exception as e:
        logger.error(f"RAG reprocess failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analysis")
def analysis_endpoint(request: AnalysisRequest):
    """
    Triggers the scoring engine to generate analysis CSV.
    """
    try:
        # Ensure the engine is actually using the model the user selected,
        # not whichever model was last active from a prior /chat request.
        llm_engine.load_model(request.model_name)

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