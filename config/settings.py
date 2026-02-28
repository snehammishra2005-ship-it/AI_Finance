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
DEFAULT_SLM = "Phi-3 Mini"

# -------------------------------------------------
# File Upload Settings
# -------------------------------------------------
ALLOWED_FILE_TYPES = ["csv", "pdf", "txt"]
MAX_UPLOAD_SIZE_MB = 10

# -------------------------------------------------
# CSV Analysis Settings
# -------------------------------------------------
ANALYSIS_CSV_COLUMNS = [
    "Model Name",
    "Data Verification Score",
    "Data Validation Score",
    "Explainability Score",
    "Persona Suitability",
    "Overall System Score",
    "Remarks"
]

# -------------------------------------------------
# Scoring Weights (Phase-2 ready)
# -------------------------------------------------
SCORING_WEIGHTS = {
    "verification": 0.2,
    "validation": 0.2,
    "explainability": 0.3,
    "persona_fit": 0.3
}

# -------------------------------------------------
# Backend (FastAPI) Settings
# -------------------------------------------------
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
BACKEND_BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

# -------------------------------------------------
# Logging
# -------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
