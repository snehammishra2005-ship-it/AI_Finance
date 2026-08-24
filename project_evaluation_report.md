# AI in Finance — Project Evaluation Report

A verified assessment of the project across Docker, backend, frontend/UI,
LightRAG, Deep Research, output quality, and security/privacy/isolation.

**Verification basis:** claims below were checked against the current code and
live runs during this work (chat, RAG, web search, analysis, Docker build),
not from assumption. Where something could not be fully verified, it is
labelled as such.

> **Update (Aug 2026) — since this assessment was written:**
> - **Per-user authentication is now implemented** (JWT login/register,
>   `backend/services/auth_service.py`, `ui/auth_view.py`) — the "no auth" finding
>   in §0, §7.1 and the recommendations below is **resolved**. Chat history and
>   uploaded documents are now scoped per user.
> - **The Groq synthesis model changed** — Groq retired `llama-3.1-8b-instant`; the
>   app now uses `openai/gpt-oss-20b` (`reasoning_effort="low"`).
> - **RAG answers are now persona-aware** (worded for the reader, figures held exact).
> - **Plain chat replies now stream** (recommendation #4, done).
> The sections below are otherwise preserved as the original point-in-time assessment.

---

## 0. Executive summary

| Area | State |
|------|-------|
| Backend (FastAPI) | ✅ Working — chat, files, RAG, research, analysis endpoints verified |
| Frontend (Streamlit) | ✅ Working — clean ChatGPT-style UI, all pages render |
| LightRAG (document Q&A) | ✅ Working — per-session isolation verified |
| Deep Research (web search) | ✅ Working — Tavily + inline citations + source list |
| Docker | ⚠️ Builds & runs; both-containers-healthy not fully re-confirmed (daemon stopped mid-check) |
| Output quality | ✅ Good, with concrete improvement areas |
| Security / auth | ✅ **Per-user JWT auth added** (was the biggest gap; see Update above) |
| Data isolation | ✅ RAG isolated per session; **chat history now scoped per user** |

The app is **functionally solid** and genuinely usable. Its original weaknesses were
**operational/security** (no login, global chat history); per-user auth has since
closed the biggest of these. Remaining operational work (rate limits, a real DB,
CORS) is tracked in `PRODUCTION_READINESS.md`.

---

## 1. Docker

**Verified this session:** the image build **succeeds** with `torch-2.13.0+cpu`,
`lightrag-hku`, and `sentence-transformers` installed; the frontend container
came up healthy (HTTP 200).

**What's good**
- `.dockerignore` keeps `venv/`, `.git/`, `data/`, `.env` out of the image
  (image dropped from ~9.9 GB toward a much smaller footprint).
- CPU-only torch (`--extra-index-url .../whl/cpu`) — ~200 MB instead of ~2.5 GB.
- Build resilience: `--timeout 120 --retries 10` + a BuildKit pip cache mount,
  after earlier builds died on pip network timeouts.
- Healthchecks on both services (python urllib, since curl isn't in the slim
  base image); frontend waits on `condition: service_healthy` so the UI never
  opens onto a dead backend.
- `hf-cache` named volume persists the embedding model (~90 MB downloads once).
- Secrets via `env_file: .env` at runtime, not baked into the image.

**Not fully verified / caveats**
- I could not re-confirm **both** containers healthy simultaneously — Docker
  Desktop stopped before the final check. Build + frontend health + config are
  verified; a full `docker compose up` end-to-end should be run once to close
  this out.
- **First backend start is slow** (embedding-model download + torch import);
  the 180 s healthcheck `start_period` covers it.

**Recommendations**
- For real deployment, don't publish backend port `8000` to the host — expose
  only the frontend and keep the backend on the internal network.
- Drop the `.:/app` bind-mount for production (it's a dev convenience that
  shadows the image with host files, including the host `venv/`).

---

## 2. Backend (FastAPI)

**Verified working:** `/`, `/chat`, `/files`, `/rag/ask`, `/rag/reprocess`,
`/research`, `/analysis`.

**What's good**
- Clean multi-provider LLM router (`llm_service.py` + `api_providers.py`):
  new vendors slot in as a subclass + config entry.
- Provider failures now **raise** and surface as HTTP 502 instead of being
  returned as fake "answers" (fixed this session) — and every sync provider
  call has a 60 s timeout.
- Graceful degradation everywhere (RAG-not-configured, web-not-configured,
  scoring-failed all return clear states, not crashes).
- `session_id` is validated with `^[a-zA-Z0-9_-]+$` before being used in a
  filesystem path — prevents path-injection into `rag_storage/sessions/`.
- No `eval` / `exec` / `os.system` / `shell=True`; the one `subprocess` use
  (backend auto-start) passes a list, not a shell string.

**Improvement areas**
- `max_tokens=512` is hard-coded in every provider — fine for chat, limiting
  for longer output; parameterize it.
- Chat providers have no retry/backoff (only the RAG async client does).
- `/chat` is a synchronous endpoint doing blocking network I/O — fine for one
  user, a bottleneck under concurrency.

---

## 3. Frontend & UI

**What's good (genuinely well done)**
- Clean, modern **ChatGPT-style layout**: slim sidebar (New chat / nav / history),
  centered chat column, model + persona pickers in a top bar, plain welcome
  screen. It looks professional, not like a default Streamlit app.
- Sensible controls: "📎 Attach a document", "📚 Answer using my uploaded
  documents", "🌐 Search the web" toggles sit together and are discoverable.
- Deep Research sources render Perplexity-style beneath the answer.
- Error states are distinct now ("The model could not answer") rather than
  silent bad answers.

**UI / UX improvements to make it more user-friendly**
1. **The three modes (chat / docs / web) are two separate checkboxes** — a user
   can tick both, and the precedence (web wins) isn't visible. A single
   segmented control ("Chat · My documents · Web") would be clearer and prevent
   ambiguous states.
2. **No streaming** — answers appear all at once after a wait. Token streaming
   would hugely improve *perceived* speed, especially with web search's extra
   step.
3. **No "thinking"/progress detail** — a plain spinner. Showing "Searching the
   web… reading results… writing…" (like the reference apps) would reassure the
   user during the multi-second research wait.
4. **Uploaded-document visibility** — after upload there's no persistent list of
   "documents in this session" the user can see or remove; they just trust it
   worked. A small "Documents (N)" panel would help.
5. **Broken model options are still selectable** — OpenRouter / Gemini /
   Anthropic appear in the dropdown but only error. Grey them out or mark them
   "unavailable".
6. **Model/persona pickers scroll out of view** in a long chat — making that bar
   sticky would keep them reachable.
7. **Sources show domain + title** but no favicon; adding favicons (as in the
   reference screenshot) would make the source list scannable at a glance.
8. **Accessibility/mobile** — the layout is desktop-first; narrow screens aren't
   tuned.

---

## 4. LightRAG (document Q&A)

**Verified working:** upload → ingest → **knowledge graph builds** (real
entities/relations, not just vector chunks) → grounded, cited answers →
**session isolation holds** (a different session gets `[no-context]`).

**What's good**
- Proper per-session isolation (see §8). The critical `workspace` bug that
  leaked data across sessions was found and fixed.
- Failure honesty: a failed ingest is reported (not silently "successful"),
  and there's a "🔄 Retry failed document indexing" recovery path.
- Bounded growth: an LRU cache caps in-memory LightRAG instances and a startup
  sweep deletes stale on-disk session dirs.
- Real filename citations (via `file_paths`).

**Improvement areas**
- Citations on **reprocessed** documents show raw text instead of the filename
  (a LightRAG purge-and-rebuild quirk) — cosmetic.
- Free-tier Groq token limits force truncation of doc context; heavy multi-doc
  use can still hit rate limits.

---

## 5. Deep Research integration

**Verified working:** web-search toggle → Tavily returns real current sources →
Groq synthesizes an answer with inline `[1][2]` citations → the UI lists the
sources beneath the reply. Web-off returns a plain answer with no sources.

**What's good**
- Reuses the existing working provider (Groq) for synthesis; Tavily supplies
  live sources. Clean fallback when the Tavily key is missing or search fails.
- Matches the intended "sources used by the model" UX (ChatGPT/Perplexity style).

**Design decision worth noting**
- Groq's own agentic/compound web-search models are **blocked on the free tier**
  (413 errors), which is why Tavily was chosen. Documented in
  `deep_research_report.md`.

**Improvement areas**
- **Single-pass** (search → synthesize once), not an iterative agent that
  reformulates queries and drills deeper.
- **Source quality varies** — Tavily returns blogs/YouTube alongside
  authoritative sources; a finance-domain allowlist or reranking would raise
  answer quality.
- **Entity conflation risk** when web results mention a similarly-named but
  different entity than an uploaded document.

---

## 6. Output quality feedback

**Good work**
- **Persona differentiation is real and sharp** — the same question yields
  genuinely different answers for Student vs. MBA vs. Senior Citizen (verified),
  driven by concrete "how to respond" rules in the persona prompts.
- **RAG answers are accurate and grounded**, with correct figures pulled from
  the source and real citations.
- **Web answers are current and cited** ([1][2] inline + source list).
- **Analysis scoring is now real** — the LLM actually grades the document on four
  dimensions (replacing the earlier random numbers), and a vague document scores
  materially lower than a detailed one (verified: 0.04 vs 0.48).

**Improvements**
- Output length capped at 512 tokens — answers can feel truncated for complex
  questions.
- Synthesis runs on Groq `openai/gpt-oss-20b` (the one reliable provider; replaced
  the retired `llama-3.1-8b-instant`) — fast and good, but not frontier-level reasoning.
- Analysis produces one row per document (honest), but doesn't chunk long
  documents into per-section scores.

---

## 7. Security, login, data protection, privacy & isolation

This is the **weakest area** and the most important to address before any
real/multi-user deployment.

### 7.1 Authentication & authorization — ✅ ADDED (per-user JWT)
> **Resolved since this assessment.** The app now has **per-user accounts** —
> register/login issue a JWT (`backend/services/auth_service.py`, `ui/auth_view.py`),
> the protected endpoints require a bearer token, and chat history and uploaded
> documents are scoped to the authenticated user. The original finding (below) is
> kept for context.

*Original finding:* there was **no login, no user accounts, no API auth of any kind**.
Consequences were: anyone reachable could burn paid API credits (Groq/Tavily), read
every saved chat, and hit the unauthenticated backend on `:8000` directly. Remaining
hardening (don't publish `:8000` publicly, add rate limiting) is tracked in
`PRODUCTION_READINESS.md`.

### 7.2 Secrets handling — ✅ Good
- `.env` is correctly **gitignored and NOT committed** to the repo (verified —
  not in the index or history).
- Docker supplies keys via `env_file` at runtime and `.dockerignore` keeps
  `.env` out of the image.

### 7.3 Network / CORS — ⚠️ Wide open
- `CORSMiddleware` uses `allow_origins=["*"]` **with** `allow_credentials=True`.
  That combination is invalid per the CORS spec (browsers reject it) and signals
  no origin restriction. Low-risk on localhost, wrong for deployment.
- Both `8000` and `8501` are published to the host in Docker.

### 7.4 Data privacy & isolation
- **RAG documents: ✅ isolated per session.** Each browser session gets its own
  `session_id` (uuid4) and its own LightRAG store; a query from another session
  returns no context. Verified with identical-content cross-session tests. The
  `session_id` is also validated to prevent path injection.
- **Chat history: ❌ global.** `load_all_histories()` reads **every**
  `chat_*.json` in one shared directory, so **every browser sees everyone's
  saved chats** in the sidebar. This is a real privacy gap for multi-user use.
- **No encryption at rest.** Chat history (JSON), analysis output (CSV), uploaded
  files, and RAG stores are all plain files on disk. Uploaded documents persist
  in `data/uploads/` indefinitely.
- **Session lifecycle:** a `session_id` lives only in Streamlit's in-memory
  session state — it resets on hard refresh, and there's no way to resume a
  session's RAG documents later.

### 7.5 Input validation — ⚠️ Partial
- File uploads are restricted by extension (`csv/pdf/txt/docx/pptx`), but the
  `MAX_UPLOAD_SIZE_MB = 10` setting **isn't enforced** (Streamlit's ~200 MB
  default applies).
- Chat input is passed to the LLM as-is (expected), and there's no
  eval/exec/SQL surface to inject into.

---

## 8. Prioritized recommendations

**Before any shared/deployed use (security):**
1. ~~**Add authentication**~~ — ✅ **done** (per-user JWT login/register).
2. ~~**Make chat history per-user**~~ — ✅ **done** (history now scoped to the
   authenticated user).
3. **Lock down CORS** to known origins and **stop publishing backend :8000** to
   the host in Docker. *(still open — see `PRODUCTION_READINESS.md`)*

**Product quality (high value, lower risk):**
4. ~~**Stream responses**~~ — ✅ **done** (plain chat streams token by token);
   research-progress display still a nice-to-have.
5. **Hide/disable the 3 non-working model options** so users don't hit errors.
6. **Unify the chat/docs/web toggles** into one segmented control.

**Robustness / cleanup:**
7. Parameterize `max_tokens`; add retry/backoff to chat providers.
8. Enforce the upload size limit; add a per-session "documents" panel.
9. Confirm a full `docker compose up` with both containers healthy end-to-end.

---

## Appendix — verification method

- Backend endpoints exercised via live HTTP calls (chat, files, rag/ask,
  research, analysis) with real provider responses.
- RAG isolation confirmed with identical-content uploads under two different
  `session_id`s (uploader gets the answer, other session gets `[no-context]`).
- Docker build verified to completion (`torch-2.13.0+cpu`, `lightrag-hku`,
  `sentence-transformers`); frontend container health = HTTP 200.
- Security claims verified by grep/`git ls-files`/config inspection of the
  current tree (a first false-positive on `.env` tracking was corrected by a
  precise re-check — `.env` is not in the repo).
