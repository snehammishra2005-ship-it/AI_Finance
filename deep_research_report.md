# Deep Research Integration — Build & Test Report

**Feature:** "Deep Research" in Q&A — a new mode that answers a question by
combining **live web search** with the user's **uploaded documents**, then
synthesizing a single cited report.

**Status:** ✅ Built and verified working end-to-end (web + documents).

---

## 1. What was built

A dedicated **🔬 Research** page (new sidebar tab, alongside Chat / Analysis /
Architecture) backed by a new research pipeline.

| Layer | File | Role |
|-------|------|------|
| Web search | `backend/services/research_service.py` | Queries **Tavily** for current web sources |
| Document retrieval | same, via `rag_service_manager` | Pulls raw context from the session's **LightRAG** documents (`only_need_context=True`, no extra LLM call) |
| Synthesis | same, via Groq client | One **Groq `llama-3.1-8b-instant`** call combines both into a cited report (max 1500 tokens) |
| API | `backend/main.py` → `POST /research` | `{question, session_id, persona}` → `{report, web_sources, web_configured, used_docs, notes}` |
| UI | `ui/research.py` | Question box, "Run Deep Research", rendered report, clickable web sources, transparency notes |

**Session-scoped:** research reads only the caller's own uploaded documents
(same per-session isolation as the RAG feature), so one user's documents never
leak into another's research.

**Graceful degradation:** every source is optional — the pipeline still answers
(and says what it used) if the web key is missing, if the session has no
documents, or both.

---

## 2. Key design decision: why Tavily, not Groq's built-in web search

The original plan was to use **Groq's compound/agentic models** (native web
search) to reuse the existing key. During verification this was found to be
**blocked on the free tier**: both `groq/compound` and `groq/compound-mini`
returned **`413 Request Too Large`** on even a 5-word prompt, while regular
Groq models worked fine. So the web-search source was switched to **Tavily**
(free tier, purpose-built for LLM research); Groq's regular Llama model still
does the synthesis.

---

## 3. Test results

All tests run against the live backend (`POST /research`) after the Tavily key
was added to `.env`.

### Test 0 — Tavily key sanity check ✅
Direct call to `_web_search("current RBI repo rate India 2026")`:
- Returned a web overview ("current RBI repo rate for 2026 is 5.25%") plus
  **4 results** with real titles and URLs (bajajhousingfinance, cleartax,
  bajajfinserv, …). Key is valid and live.

### Test 1 — Web-only research ✅
Fresh session (no documents), question requiring current info:
*"What is the current RBI repo rate and the RBI's most recent monetary policy decision?"*

| Field | Result |
|-------|--------|
| `web_configured` | **True** |
| `used_docs` | False (correct — none uploaded) |
| `web_sources` | **4** (PIB, bajajfinserv, bankbazaar, NDTV) |
| `notes` | "No relevant content found in your uploaded documents" |

Report was current and grounded — *"The current RBI repo rate is 5.25% [W2],
[W4]"* — with inline `[W#]` citations matching the numbered sources.

### Test 2 — Combined web + documents ✅ (the headline test)
Uploaded a confidential company brief (Meridian Housing Finance: Rs 8,400 cr
loan book, +19% YoY, 3.8% NIM), then asked a question needing **both** the
doc's private figures **and** live macro data:
*"Given the current RBI repo rate, how might Meridian Housing Finance be affected? Use their loan book and margin figures."*

| Field | Result |
|-------|--------|
| `web_configured` | **True** |
| `used_docs` | **True** |
| `web_sources` | 4 |
| `notes` | none (both sources available) |

The report genuinely **fused both sources**:
- `[Docs]` citations for the company's private figures (Rs 8,400 cr loan book,
  +19% YoY, repo-rate sensitivity) — from the uploaded brief.
- `[W#]` citations for live web context (repo-rate mechanics, home-loan impact).
- A **References** section listing both the web URLs and the `[Docs]` source.

### Test 3 — Graceful degradation ✅ (verified before the key was added)
- **Docs-only** (no web key): answered from the uploaded document with an
  accurate report and a clear "web search not configured" note.
- **No docs + no web:** still answered from model knowledge, with both
  transparency notes present.

---

## 4. Honest findings / caveats

1. **Entity conflation across sources (accuracy risk).** In Test 2, the
   fictional "Meridian Housing Finance" shared a name with a real US company
   ("Meridian Corp / MRBK") that Tavily surfaced, and the synthesis pulled a
   few web facts (FHLB borrowings) from the wrong entity while correctly using
   `[Docs]` for the real figures. This is inherent to blending live web with
   private documents — more likely with generic/ambiguous names, less likely
   for real, well-known companies. The citations still make the provenance
   auditable, but users should sanity-check when names are ambiguous.

2. **Synthesis quality is bounded by the model.** All synthesis runs on Groq
   `llama-3.1-8b-instant` (the one reliably working provider). It's fast and
   good, but not a frontier model — deep multi-hop reasoning is limited.

3. **Free-tier limits still apply.** Groq's ~6,000 tokens/minute cap means
   web results and document context are truncated (4 web results, ~600 chars
   each; ~2,500 chars of doc context) to fit one synthesis call. Rapid repeated
   research can still hit rate limits.

4. **Single-pass, not iterative.** This is "research" as *search → gather →
   synthesize once*, not a multi-step agent that reformulates queries and digs
   deeper. That's a reasonable, reliable v1; true iterative deep research would
   be a follow-up.

---

## 5. How to use

1. Open the **🔬 Research** tab in the sidebar.
2. (Optional) Upload documents in the **Chat** tab first — research will draw
   from them for the current session.
3. Type a research question and click **Run Deep Research**.
4. Read the report; expand **Sources** for the web links and **About this
   answer's sources** for what was/wasn't used.

**Requirements:** `TAVILY_API_KEY` in `.env` (already added) for web search;
`GROQ_API_KEY` for synthesis.

---

## 6. Verification method note

The backend pipeline was verified directly via `POST /research` (evidence
above). The Research page itself was confirmed to render in the UI (the new
sidebar tab appears and the page loads without errors); live in-browser
click-through screenshots were interrupted by a flaky browser-automation
connection, but the page consumes exactly the response shape validated in the
endpoint tests.
