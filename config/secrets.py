"""
Centralized secret handling.

All secrets (LLM API keys, the JWT signing key, the Tavily key) are described in
one place here, and resolved through a single accessor so the app has one clear
contract for *what* secrets exist and *where* they come from.

Resolution order for a secret NAME:
  1. `NAME_FILE` — a path whose file contents are the secret. This is how real
     secret stores hand secrets to a process without ever putting the value in
     an environment variable or baking it into the image: Docker secrets and
     Kubernetes secrets mount files under /run/secrets, and Vault/CSI sidecars
     write files too. Preferred in production.
  2. `NAME` — a plain environment variable (python-dotenv loads these from a
     local `.env` for development).

`hydrate_env_from_files()` runs once at import of config.settings and copies any
`*_FILE` secret into `os.environ[NAME]`, so the existing `os.environ.get(...)`
reads scattered through the provider adapters transparently gain file-based
secret support with no change at those call sites.

To plug in a managed store (AWS Secrets Manager, GCP Secret Manager, Vault API),
add a resolver to `get_secret()` — nothing else needs to change.

Secret VALUES are never logged; use `redact()` for any diagnostic output.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Single source of truth for the secrets the app uses.
# name -> (human description, required?)
KNOWN_SECRETS = {
    "GROQ_API_KEY": ("Groq API key — default LLM + RAG/metric extraction", True),
    "OPENROUTER_API_KEY": ("OpenRouter API key", False),
    "GEMINI_API_KEY": ("Google Gemini API key", False),
    "ANTHROPIC_API_KEY": ("Anthropic API key", False),
    "CEREBRAS_API_KEY": ("Cerebras API key", False),
    "MISTRAL_API_KEY": ("Mistral API key", False),
    "TAVILY_API_KEY": ("Tavily web-search API key (enables 'Search the web')", False),
    "JWT_SECRET": ("JWT signing secret for auth tokens", False),  # required only in prod
}


def get_secret(name: str, default=None):
    """Resolve a secret by name (see module docstring for the order)."""
    file_path = os.environ.get(f"{name}_FILE")
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                value = f.read().strip()
            if value:
                return value
            logger.warning("Secret file for %s is empty: %s", name, file_path)
        except OSError as e:
            logger.warning("Could not read secret %s from %s: %s", name, file_path, e)

    value = os.environ.get(name)
    if value:
        return value
    return default


def has_secret(name: str) -> bool:
    return bool(get_secret(name))


def hydrate_env_from_files() -> None:
    """
    Copy any `*_FILE`-provided secret into os.environ[NAME] so downstream
    os.environ reads (provider SDK clients, Tavily) pick it up without change.
    `*_FILE` takes precedence (same as get_secret), so a mounted secret file
    wins over a stale plain env var. Idempotent.
    """
    for name in KNOWN_SECRETS:
        file_path = os.environ.get(f"{name}_FILE")
        if not file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                value = f.read().strip()
            if value:
                os.environ[name] = value
        except OSError as e:
            logger.warning("Could not hydrate %s from %s: %s", name, file_path, e)


def redact(value: str) -> str:
    """Mask a secret for safe logging: keep a few edge chars only."""
    if not value:
        return "(unset)"
    if len(value) <= 6:
        return "***"
    return f"{value[:3]}…{value[-2:]}"


def log_config_summary() -> None:
    """Log which secrets are configured (never their values) and warn about any
    required secret that's missing. Call once at startup."""
    for name, (desc, required) in KNOWN_SECRETS.items():
        present = has_secret(name)
        if present:
            logger.info("Secret %s: configured (%s)", name, redact(get_secret(name)))
        elif required:
            logger.warning("Secret %s is MISSING but required — %s", name, desc)
        else:
            logger.info("Secret %s: not set (optional) — %s", name, desc)
