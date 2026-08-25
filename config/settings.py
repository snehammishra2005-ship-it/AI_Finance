"""
Global application settings for AI in Finance project.

This file contains only configuration constants.
DO NOT import Streamlit or UI code here.
"""

import os
import logging
from pathlib import Path

from config.secrets import get_secret, hydrate_env_from_files

logger = logging.getLogger(__name__)

# Resolve any *_FILE-provided secrets into the environment up front, so every
# downstream os.environ read (provider SDK clients, Tavily, etc.) transparently
# supports file-based secret stores (Docker/Kubernetes secrets, Vault).
hydrate_env_from_files()

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
DEFAULT_SLM = "GPT-OSS 20B (Groq)"

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
# Authentication (per-user accounts)
# -------------------------------------------------
# SQLite user store. Overridable via env so tests can point at a throwaway DB
# and a real deployment can move it onto a mounted volume. (Migrates to Postgres
# per the production-readiness plan, P1 #6.)
AUTH_DB_PATH = os.getenv("AUTH_DB_PATH", str(DATA_DIR / "auth.db"))

# JWT signing. HS256 with a shared secret. Token lifetime is in hours.
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))


def _load_or_create_jwt_secret() -> str:
    """
    The JWT signing secret, resolved via the secrets layer (env or a *_FILE
    secret store). In production it MUST be provided explicitly — we refuse to
    boot on a generated one, since a per-process secret would silently
    invalidate everyone's sessions on restart and can't be shared across
    replicas. For local/dev convenience only, an unset secret is generated once
    and persisted to data/.jwt_secret so tokens survive a restart.
    """
    secret = get_secret("JWT_SECRET")
    if secret:
        return secret

    if ENVIRONMENT == "production":
        raise RuntimeError(
            "JWT_SECRET is not set. In production it must be provided explicitly "
            "(env var or a JWT_SECRET_FILE secret) — refusing to start with a "
            "generated key."
        )

    import secrets as _secrets

    logger.warning(
        "JWT_SECRET not set — generating a development key (data/.jwt_secret). "
        "Set JWT_SECRET explicitly before any real deployment."
    )
    secret_file = DATA_DIR / ".jwt_secret"
    try:
        if secret_file.exists():
            existing = secret_file.read_text(encoding="utf-8").strip()
            if existing:
                return existing
        generated = _secrets.token_urlsafe(48)
        secret_file.write_text(generated, encoding="utf-8")
        return generated
    except OSError:
        # Read-only filesystem: fall back to an in-process secret (tokens won't
        # survive a restart, but the app still runs).
        return _secrets.token_urlsafe(48)


JWT_SECRET = _load_or_create_jwt_secret()

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
