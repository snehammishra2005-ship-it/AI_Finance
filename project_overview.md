# AI in Finance — Project Overview & Verified Evaluation

_Single source of truth for what the project is and how well it works. Consolidates the
former `project_summary.md`, `project_evaluation_report.md`, and
`output_quality_verified_report.md` into one current document._

**Last updated:** August 2026.
**Verification basis:** functional claims were checked against the current code and live runs
(chat, RAG, web search, analysis, Docker build) — not assumed. Point-in-time probe figures
(dates noted inline) are preserved where still useful. Operational hardening still to do is
tracked separately in [`PRODUCTION_READINESS.md`](PRODUCTION_READINESS.md); the document Q&A
quality benchmark against NotebookLM lives in
[`Evaluation with NotebookLM.md`](Evaluation%20with%20NotebookLM.md).

---

## 1. Overview

An AI-powered financial assistant with a **Streamlit** frontend and a **FastAPI** backend.
Signed-in users chat with a finance-tuned assistant (selectable personas), upload financial
documents for RAG-based Q&A, run web-augmented research, and generate automated
document-scoring and metric-extraction reports.

The language models are **cloud-hosted APIs**, not a local model — no model download or GPU
requirement. (An earlier prototype used a local `TinyLlama-1.1B`; the app no longer does. The
`transformers`/`torch` dependencies remain only for the local sentence-embedding model used by
RAG.)

---

## 2. Architecture

### Backend (FastAPI) — `backend/main.py`
- **`/auth/*`** — register/login; issues a JWT and scopes each user's history and documents to
  their own account (`backend/services/auth_service.py`).
- **`/chat`** — chat with the selected provider/persona; multi-turn history, optional Tavily
  **web search**, and a **blend** mode grounding the answer in both uploaded documents and live
  web results (cited).
- **`/chat/stream`** — the same plain-chat answer, streamed token by token.
- **`/files`** — upload + text extraction (PDF, DOCX, PPTX, XLSX/XLS, CSV, TXT, images via OCR),
  then per-session RAG indexing.
- **`/rag/ask`** — question answering grounded strictly in the session's documents, **worded for
  the selected persona** (with a hard guardrail that keeps every figure exact and never invents
  one).
- **`/rag/reprocess`** — retries documents whose indexing previously failed (e.g. a rate limit).
- **`/metrics`** — extracts explicitly-stated financial metrics as structured rows.
- **`/analysis`** — scoring engine → CSV report (verification / validation / explainability /
  persona-suitability + weighted system score).

### LLM routing — `backend/services/llm_service.py` + `api_providers.py`
A single `LLMEngine` router dispatches to one of six providers and **falls back transparently**
to the next configured provider if the selected one fails, so a single provider outage doesn't
break chat. Providers: **Groq** (`openai/gpt-oss-20b`, default — replaced the retired
`llama-3.1-8b-instant`), **OpenRouter** (GPT-5.5), **Google** (Gemini 3 Flash, via the
`google-genai` SDK), **Anthropic** (Claude 3 Haiku), **Cerebras** (GPT-OSS 120B), and **Mistral**
(Mistral Small). Configured in `config/slm_config.py`; keys come from `.env`.

### RAG — `backend/services/rag/`
LightRAG-based, with **per-session isolation** (each session has its own working dir +
workspace), structure-aware chunking, table preservation, duplicate/replace handling, an LRU
cache of active sessions, and a stale-session sweep. Embeddings use `BAAI/bge-small-en-v1.5`
(384-d) run locally on CPU. Answers are persona-aware (see `RAG_implementation.md`).

### Frontend (Streamlit) — `ui/app.py`
`ui/app.py` is the single entry point: it renders the UI **and** boots the backend as a child
process if it isn't already running (guarded by a lock file). Components: auth
(`ui/auth_view.py`), chat (`ui/chat.py`), file upload + metric extraction (`ui/file_upload.py`),
analysis view with a score chart (`ui/analysis_view.py`), sidebar with history (`ui/sidebar.py`),
and an architecture view.

---

## 3. Key features

1. **Per-user accounts** — register/login with JWT auth; chat history and uploaded documents are
   isolated per user.
2. **Persona-driven chat** — selectable audience personas drive tone/length via a style-guide
   system prompt layered on a safety-focused base prompt (accuracy first, never invent numbers,
   educational-not-advice). Plain chat replies **stream** token by token.
3. **Multi-provider LLM routing** with automatic fallback.
4. **Multi-format document extraction** with table preservation and OCR fallback.
5. **Per-session RAG document Q&A** — **persona-aware** (answers reworded for the reader, figures
   held exact) — plus a web/document blend mode with cited sources.
6. **Financial metric extraction** and **document scoring** with CSV export.
7. **Chat history** save/load with first-question titles.

---

## 4. Verified evaluation — status at a glance

| Area | State |
|------|-------|
| Backend (FastAPI) | ✅ Working — auth, chat, files, RAG, research, analysis endpoints verified |
| Frontend (Streamlit) | ✅ Working — clean ChatGPT-style UI, all pages render |
| Chat quality + streaming | ✅ Accurate; plain chat streams token-by-token (verified in browser) |
| Advice guardrail | ✅ Enforced by a deterministic backstop (+ unit tests) |
| Provider routing + fallback | ✅ Works; rescues requests aimed at dead providers |
| LightRAG (document Q&A) | ✅ Accurate, cited, no hallucination; per-session isolation verified |
| Deep Research (web) | ✅ Tavily + inline citations + source list |
| Metric extraction / scoring | ✅ Precise (5/5); honest fallback when the model can't score |
| Security / auth | ✅ Per-user JWT auth; CORS restricted (configurable) |
| Data isolation | ✅ RAG per session; chat history scoped per user |
| Docker | ⚠️ Builds & runs; both-containers-healthy-simultaneously not fully re-confirmed |
| Provider availability | ⚠️ 3/6 solid (Groq, Gemini, Mistral); 1 low-credit; 2 out of credit |
| RAG / web latency | ⚠️ Slow (~20–28 s RAG, ~12–15 s web) — inherent to free-tier multi-step |

The app is **functionally solid and genuinely usable.** Its original weaknesses were
operational/security (no login, global chat history); per-user auth has closed the biggest of
those. Remaining operational work (rate limits, a real DB, not publishing `:8000`) is tracked in
`PRODUCTION_READINESS.md`.

---

## 5. Per-area findings

### 5.1 Backend
- Clean multi-provider router: new vendors slot in as a subclass + config entry.
- Provider failures **raise** and surface as HTTP 502 rather than being returned as fake
  "answers"; every sync provider call has a 60 s timeout.
- Graceful degradation everywhere (RAG-not-configured, web-not-configured, scoring-failed return
  clear states, not crashes).
- `session_id` is validated with `^[a-zA-Z0-9_-]+$` before use in a filesystem path (prevents
  path injection). No `eval`/`exec`/`os.system`/`shell=True`.
- **Open:** `max_tokens=512` is hard-coded per provider (parameterize it); chat providers have no
  retry/backoff (only the RAG async client does); `/chat` is synchronous (a bottleneck under
  concurrency).

### 5.2 Frontend & UI
- Clean, modern ChatGPT-style layout: slim sidebar, centered chat column, model + persona
  pickers in a top bar. Discoverable toggles ("📚 Answer using my uploaded documents", "🌐 Search
  the web"). Deep Research sources render Perplexity-style beneath the answer. Distinct error
  states.
- **Open UI improvements:** unify the chat/docs/web checkboxes into one segmented control; add a
  persistent "documents in this session" panel; grey out providers that are out of credit;
  add source favicons; tune for mobile/accessibility.

### 5.3 LightRAG (document Q&A)
- Verified: upload → ingest → **knowledge graph builds** (real entities/relations) → grounded,
  cited answers → **session isolation holds** (a different session gets `[no-context]`).
- Failure honesty: a failed ingest is reported (not silently "successful"), with a "🔄 Retry
  failed document indexing" recovery path. Bounded growth via LRU cache + startup sweep. Real
  filename citations.
- **Open:** citations on *reprocessed* documents show raw text instead of the filename (cosmetic
  LightRAG quirk); free-tier Groq token limits force truncation of large-doc context (see the
  NotebookLM Test 3 finding — a large document can exceed Groq's per-minute token budget).

### 5.4 Deep Research (web)
- Verified: web-search toggle → Tavily returns live sources → Groq synthesizes with inline
  `[1][2]` citations → the UI lists sources. Web-off returns a plain answer.
- Groq's own agentic web-search models are blocked on the free tier (413), which is why Tavily
  was chosen (see `deep_research_report.md`).
- **Open:** single-pass (not an iterative agent); Tavily source quality varies (a finance-domain
  allowlist/reranking would help); entity-conflation risk vs. uploaded docs.

### 5.5 Output quality (verified live)
- **Chat:** leads with the point, clean Markdown, defines terms, honors persona/length.
  Correctly refuses real-time data it can't have (no fabricated numbers).
- **Advice guardrail:** a forced "answer only yes or no" buy/sell question still returns the
  required educational framing, enforced by a deterministic backstop (`advice_safety_note`, 7
  unit tests). A general factual short answer is unaffected.
- **Streaming:** a 3-tip answer arrived as ~76 incremental chunks over `POST /chat/stream`;
  multi-byte characters (₹) survive chunk boundaries. Verified rendering live in a browser.
- **RAG accuracy:** on a synthetic report, correct cited answers for revenue/growth, dividend &
  date, and facts present; correctly abstained on a fact **not** in the document.
- **Metric extraction:** 5/5 metrics with currency and periods; "never invent metrics" held.
- **Scoring:** real 0–1 scores across four dimensions + weighted System Score; on unparseable
  model output it writes nulls + an honest "scoring failed" remark rather than inventing numbers.

### 5.6 Testing
- Offline unit suite under `tests/` — **all passing** via `python -m unittest discover -s tests`,
  no network or API keys required. Covers citation stripping, web/blend prompt assembly, score
  parsing, metric parsing, file-type magic-byte detection, table formatting, persona loading,
  history-title derivation, the advice-guard backstop, per-user auth, and settings/backend
  consistency.

### 5.7 Docker
- Image build **succeeds** (CPU-only torch, `lightrag-hku`, `sentence-transformers`); frontend
  container came up healthy (HTTP 200). `.dockerignore` keeps `venv/`, `.git/`, `data/`, `.env`
  out; healthchecks on both services; `hf-cache` volume persists the embedding model; secrets via
  `env_file` at runtime.
- **Open:** re-confirm both containers healthy simultaneously in one `docker compose up`
  (Docker Desktop stopped mid-check last time). First backend start is slow (embedding-model
  download + torch import; the 180 s healthcheck `start_period` covers it). For production, don't
  publish backend `:8000` to the host and drop the dev `.:/app` bind-mount.

---

## 6. LLM providers — verified live (probe of 2026-08-02)

| Provider (model) | Result | Notes |
|---|---|---|
| **Groq** — `openai/gpt-oss-20b` | ✅ Working | Default; fastest, most reliable |
| **Google** — Gemini 3 Flash | ✅ Working | Fixed — migrated to `google-genai`, thinking disabled, empty-response guarded |
| **Mistral** — Mistral Small | ✅ Working | Fast |
| **OpenRouter** — GPT-5.5 | ⚠️ Low credit | Returns empty/`402` — account nearly out of credit |
| **Anthropic** — Claude 3 Haiku | ❌ Out of credit | `400 — credit balance too low` |
| **Cerebras** — GPT-OSS 120B | ❌ Out of credit | `402 — payment required` |

The fallback chain transparently rescues a request routed to a dead/degraded provider — a chat
aimed at Anthropic/Cerebras/OpenRouter is answered by the next configured provider.

---

## 7. Security & data isolation

- **Authentication — ✅ per-user JWT.** Register/login issue a JWT
  (`backend/services/auth_service.py`, `ui/auth_view.py`); protected endpoints require a bearer
  token; chat history and uploaded documents are scoped to the authenticated user.
- **Secrets — ✅ good.** `.env` is gitignored and not committed; Docker supplies keys via
  `env_file` at runtime and `.dockerignore` keeps `.env` out of the image.
- **CORS — ✅ restricted.** A preflight from the app origin is allowed; an untrusted origin is
  rejected. Overridable via `CORS_ALLOW_ORIGINS`. (Replaced the earlier unsafe
  `allow_origins=["*"]` + `allow_credentials=True` combination.)
- **RAG documents — ✅ isolated per session** (own `session_id` + LightRAG store; cross-session
  queries return no context; `session_id` validated against path injection).
- **Still open (see `PRODUCTION_READINESS.md`):** no encryption at rest; the `MAX_UPLOAD_SIZE_MB`
  cap isn't fully enforced; add rate limiting; move the file-based auth/history stores to a real
  database; don't publish backend `:8000` publicly.

---

## 8. Known limitations

1. **Provider credit:** only Groq, Gemini, and Mistral are fully working; OpenRouter is nearly
   out and Anthropic/Cerebras are out. They stay selectable and are covered by fallback.
2. **RAG/web latency:** ~20–28 s (RAG) and ~12–15 s (web) per answer — inherent to free-tier
   multi-step retrieval + synthesis; streaming is not applied to these modes.
3. **Large documents on Groq:** a very large document can exceed Groq's free-tier per-minute
   token limit at retrieval time (surfaced by NotebookLM Test 3); full-RAG on a larger-quota
   provider handles it.
4. **No learned reranker:** recall is unaffected for current corpus sizes, but no reranking is
   performed.
5. **Metric visualization:** metrics are shown as a table (mixed $/% units make a single-axis
   chart misleading); only the 0–1 analysis scores are charted.

---

## 9. Related documents

- [`README.md`](README.md) — setup and run instructions.
- [`PRODUCTION_READINESS.md`](PRODUCTION_READINESS.md) — remaining hardening before a shared deployment.
- [`RAG_implementation.md`](RAG_implementation.md), [`api_integration_report.md`](api_integration_report.md),
  [`deep_research_report.md`](deep_research_report.md), [`document_processing_report.md`](document_processing_report.md),
  [`docker_implementation_verification.md`](docker_implementation_verification.md) — per-feature detail.
- [`Evaluation with NotebookLM.md`](Evaluation%20with%20NotebookLM.md) + `test 1 results.md`, `test 2 results.md`,
  [`Test3_report.md`](Test3_report.md) — document-Q&A quality benchmarked against NotebookLM.
