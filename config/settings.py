"""
Global application settings for AI in Finance project.

This file contains only configuration constants.
DO NOT import Streamlit or UI code here.
"""

import os
from pathlib import Path

# -------------------------------------------------
# Project Root
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# -------------------------------------------------
# Data Directories
# -------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
HISTORY_DIR = DATA_DIR / "history"
ANALYSIS_OUTPUTS_DIR = DATA_DIR / "analysis_outputs"

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# Application Settings
# -------------------------------------------------
APP_NAME = "AI in Finance"
APP_VERSION = "1.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# -------------------------------------------------
# UI Defaults
# -------------------------------------------------
DEFAULT_PERSONA = "Student"
DEFAULT_SLM = "Llama 3.1 8B Instant (Groq)"

# -------------------------------------------------
# File Upload Settings
# -------------------------------------------------
# Kept in sync with what FileProcessor actually accepts and with the backend's
# real MAX_UPLOAD_BYTES cap (see backend/main.py). These are the source of
# truth for the UI file_uploader's accepted types.
ALLOWED_FILE_TYPES = [
    "pdf", "docx", "pptx", "xlsx", "xls", "csv", "txt",
    "png", "jpg", "jpeg", "tiff", "tif", "bmp", "webp", "gif",
]
MAX_UPLOAD_SIZE_MB = 25

# NOTE: The document-scoring dimensions and their weights live in
# ScoringEngine._WEIGHTS (backend/services/scoring_engine.py), which is the
# single source of truth. They are intentionally NOT duplicated here to avoid
# the two drifting apart.

# -------------------------------------------------
# Backend (FastAPI) Settings
# -------------------------------------------------
# Overridable via env so Docker Compose can point the frontend container at
# the separate "backend" service instead of localhost (see BACKEND_HOST /
# BACKEND_API_URL in docker-compose.yml).
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
BACKEND_BASE_URL = os.getenv("BACKEND_API_URL", f"http://{BACKEND_HOST}:{BACKEND_PORT}")

# -------------------------------------------------
# Logging
# -------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
