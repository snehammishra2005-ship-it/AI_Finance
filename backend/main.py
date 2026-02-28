
"""
FastAPI backend entry point for AI in Finance project.

This backend handles:
- Chat requests (SLM via Transformers)
- File processing (Text Extraction)
- Analysis & scoring (CSV Generation)
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import logging

from config.settings import APP_NAME, APP_VERSION
from backend.services.file_processor import FileProcessor
from backend.services.scoring_engine import ScoringEngine
from backend.services.llm_service import llm_engine

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
    slm_model: str = "TinyLlama-1.1B"

class AnalysisRequest(BaseModel):
    filename: str
    text_content: str
    model_name: str = "TinyLlama-1.1B"

# -------------------------------------------------
# Endpoints
# -------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "running",
        "service": "AI in Finance Backend",
        "model_loaded": llm_engine._pipe is not None
    }

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    """
    Handles chat requests using the integrated SLM.
    """
    try:
        logger.info(f"Chat Request: {request.message[:20]}... | Persona: {request.persona}")
        
        # Generate response using the LLM Engine
        response_text = llm_engine.generate_response(
            message=request.message,
            persona=request.persona
        )
        
        return {
            "response": response_text,
            "model": request.slm_model
        }
    except Exception as e:
        logger.error(f"Chat logic failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files")
async def file_processing_endpoint(file: UploadFile = File(...)):
    """
    Receives an uploaded file, determines type, and extracts text.
    """
    try:
        content = await file.read()
        text = FileProcessor.extract_text(content, file.filename)
        
        return {
            "filename": file.filename,
            "message": "File processed successfully",
            "extracted_text_preview": text[:200],
            "full_text": text 
        }
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analysis")
def analysis_endpoint(request: AnalysisRequest):
    """
    Triggers the scoring engine to generate analysis CSV.
    """
    try:
        # Pass the LLM engine to the scoring logic so it can generate remarks
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
