# AI in Finance — Project Summary

## Overview
An AI-powered financial assistant with a Streamlit frontend and a FastAPI
backend. Users chat with a finance-tuned assistant (with selectable personas),
upload financial documents for RAG-based Q&A, run web-augmented research, and
generate automated document-scoring and metric-extraction reports.

The language models are **cloud-hosted APIs**, not a local model — there is no
model download or GPU requirement. (An earlier prototype used a local
`TinyLlama-1.1B` model via Transformers; the app no longer does, and the
`transformers`/`torch` dependencies remain only for the local sentence-embedding
model used by RAG.)

## Architecture

### Backend (FastAPI) — `backend/main.py`
RESTful endpoints:
- **`/auth/*`** — register/login; issues a JWT and scopes each user's history and
  documents to their own account.
- **`/chat`** — chat with the selected provider/persona. Supports multi-turn
  history, optional Tavily **web search**, and a **blend** mode that grounds the
  answer in both the session's uploaded documents and live web results (cited).
- **`/chat/stream`** — the same plain-chat answer, streamed token by token.
- **`/files`** — upload + text extraction (PDF, DOCX, PPTX, XLSX/XLS, CSV, TXT,
  and images via OCR), then per-session RAG indexing.
- **`/rag/ask`** — question answering grounded strictly in the current session's
  uploaded documents, **worded for the selected persona** (with a hard guardrail
  that keeps every figure exact and never invents one).
- **`/rag/reprocess`** — retries documents whose indexing previously failed
  (e.g. a provider rate limit).
- **`/metrics`** — extracts explicitly-stated financial metrics as structured rows.
- **`/analysis`** — scoring engine → CSV report (verification / validation /
  explainability / persona-suitability + weighted system score).

### LLM routing — `backend/services/llm_service.py` + `api_providers.py`
A single `LLMEngine` router dispatches to one of six providers and **falls back
transparently** to the next configured provider if the selected one fails
(e.g. a rate limit or billing error), so a single provider outage doesn't break
chat. Providers: **Groq** (GPT-OSS 20B, default), **OpenRouter** (GPT-5.5),
**Google** (Gemini 3 Flash, via the `google-genai` SDK), **Anthropic**
(Claude 3 Haiku), **Cerebras** (GPT-OSS 120B), and **Mistral** (Mistral Small).
Configured in `config/slm_config.py`; keys come from `.env`.

### RAG — `backend/services/rag/`
LightRAG-based, with **per-session isolation** (each session has its own
working dir + workspace), structure-aware chunking, table preservation,
duplicate/replace handling, an LRU cache of active sessions, and a stale-session
sweep. Embeddings use `BAAI/bge-small-en-v1.5` (384-d) run locally.

### Frontend (Streamlit) — `ui/app.py`
`ui/app.py` is the single entry point: it renders the UI **and** boots the
backend as a child process if it isn't already running (guarded by a lock file).
Components: chat (`ui/chat.py`), file upload + metric extraction
(`ui/file_upload.py`), analysis view with a score chart (`ui/analysis_view.py`),
sidebar with history (`ui/sidebar.py`), and an architecture view.

## Key Features
1. **Per-user accounts** — register/login with JWT auth; chat history and uploaded
   documents are isolated per user.
2. **Persona-driven chat** — selectable audience personas drive tone/length via a
   style-guide system prompt layered on a safety-focused base prompt (accuracy
   first, never invent numbers, educational-not-advice). Plain chat replies **stream**.
3. **Multi-provider LLM routing** with automatic fallback.
4. **Multi-format document extraction** with table preservation and OCR fallback.
5. **Per-session RAG** document Q&A — **persona-aware** (answers reworded for the
   reader, figures held exact) — plus web/document blend mode with cited sources.
6. **Financial metric extraction** and **document scoring** with CSV export.
7. **Chat history** save/load with first-question titles.

## Testing
Offline unit tests live in `tests/` (run `python -m unittest discover -s tests`).
They cover the deterministic logic — parsing, formatting, file-type detection,
prompt assembly, persona/history helpers, and config consistency — with no
network calls or API keys required. Ad-hoc live smoke scripts (`verify_*.py`)
exercise the real provider APIs.

## Known Limitations
- Two providers (Anthropic, Cerebras) may be out of API credit depending on the
  account; fallback covers for them.
- RAG and web-augmented answers have noticeable latency (multi-step retrieval +
  synthesis on free tiers).
- Per-user auth is now in place (JWT), but other hardening remains before a shared
  deployment — restrict CORS (`CORS_ALLOW_ORIGINS`), add rate limiting, and move the
  file-based auth/history stores to a real database (see `PRODUCTION_READINESS.md`).
