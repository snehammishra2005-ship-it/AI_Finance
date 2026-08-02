# AI in Finance — Verified Output-Quality Report

**Date:** 2026-08-02
**Method:** Every claim below was verified by running the project's own code against
the live APIs (using the repo's `.env` keys and `venv`), not by reading the docs.
Verification covered all six LLM providers, the chat path, the scoring engine, the
metric extractor, and the full RAG ingest→query pipeline.

---

## 1. Verdict

The application **works and produces good-quality, grounded output** on its core
paths. Chat is accurate and well-formatted, document Q&A (RAG) retrieves and cites
correctly and refuses to answer what isn't in the document, and financial-metric
extraction is precise. The main issues are **operational** (2 of 6 model providers
are out of credits), **latency** (RAG answers take 20–28 s), and **stale/inconsistent
docs and config**, not core correctness.

| Area | Status | Evidence |
|------|--------|----------|
| Chat quality & guardrails | ✅ Good | Live calls, section 3 |
| Provider routing + fallback | ✅ Works (masks failures gracefully) | Live, section 2 |
| RAG document Q&A | ✅ Accurate, cited, no hallucination | Live, section 4 |
| Financial metric extraction | ✅ Precise (5/5 metrics correct) | Live, section 5 |
| Document scoring engine | ✅ Works, honest fallback | Live, section 6 |
| Provider availability | ⚠️ 4/6 live; 2 out of credit | Live, section 2 |
| Latency (web + RAG) | ⚠️ Slow | Live, sections 2 & 4 |
| Docs / config consistency | ❌ Stale in places | Static, section 8 |

---

## 2. LLM Providers — verified live (direct call, no fallback)

| Provider (model) | Result | Latency | Notes |
|---|---|---|---|
| **Groq** — Llama 3.1 8B Instant | ✅ Working | ~0.6–2.5 s | Default; fastest & most reliable |
| **OpenRouter** — GPT-5.5 | ✅ Working | ~3–15 s | Works; higher latency |
| **Google** — Gemini 3 Flash | ⚠️ Works but fragile | ~12.6 s | Returned "OK" at a normal token budget, but `GeminiProvider` **crashes on an empty/truncated response** (`response.text` quick-accessor raises). Also uses the **deprecated** `google.generativeai` SDK. |
| **Anthropic** — Claude 3 Haiku | ❌ Failing | — | `400 — credit balance too low` |
| **Cerebras** — GPT-OSS 120B | ❌ Failing | — | `402 — payment required` |
| **Mistral** — Mistral Small | ✅ Working | ~0.5–1.2 s | Works, fast |

**Key finding on resilience:** the multi-provider **fallback chain genuinely works**.
In testing, requests routed to Anthropic and Cerebras failed on billing, and the
engine transparently fell back to a working provider and still returned a correct
answer. This is a real strength — a single provider being down doesn't break chat.
(It also means a naive health check can *hide* a dead provider; the failure only
shows in logs.)

---

## 3. Chat Output Quality — verified live

Three probe questions were sent through the real chat path (`generate_response_with_model`,
Student persona, default model):

- **Definition ("What is inflation?")** → Accurate, plain-language, correctly
  bolded key term, 2 sentences as asked. **Good.**
- **Hallucination guard ("exact closing price of Apple on 2025-07-14?")** →
  Correctly **refused**, stated it lacks real-time/future data, and pointed to
  reliable sources. No fabricated number. **Good** — the "never invent numbers"
  rule in the system prompt holds up.
- **Advice guard ("Should I put all my savings into Tesla? yes or no")** →
  Answered just **"No."** Safe direction, but see the weakness below.

**Strengths verified:** answers lead with the point, use clean Markdown, define
terms, and honor persona/length instructions. The base system prompt
([llm_service.py](backend/services/llm_service.py)) enforces accuracy, grounding,
and an educational (non-advice) stance, and in practice it does.

---

## 4. RAG / Document Q&A — verified live (ingest → 4 queries)

A synthetic quarterly report was ingested (indexed **with** the knowledge graph in
6.1 s) and queried:

| Question | Answer | Correct? |
|---|---|---|
| Q2 revenue & growth | "$12.4M … 27% increase over Q2 2024 ($9.76M)" + citation | ✅ |
| Dividend & date | "$0.15 per share, payable September 2025" | ✅ |
| New distribution centers | "Texas and Ohio" | ✅ |
| Employee headcount (**not in doc**) | "the provided context does not contain any information…" | ✅ (no hallucination) |

**Strengths:** correct retrieval, inline source citations, and — importantly — it
**declines to answer what isn't in the document** instead of guessing. Per-session
isolation, structure-aware chunking, table preservation, and duplicate/replace
handling are all implemented in [rag_service.py](backend/services/rag/rag_service.py).

**Weaknesses:** each RAG query took **20–28 s** (mix-mode graph+vector retrieval +
Groq synthesis) — noticeably slow for interactive use. LightRAG also logs
**"Rerank is enabled but no rerank model is configured"** on every query, so
retrieval quality is left on the table.

---

## 5. Financial Metric Extraction — verified live

From a 5-fact sample, the extractor returned **5/5 metrics correctly** with currency
and period: Revenue $4.2M (FY2024), Net profit $600K, Operating margin 22%, Total
assets $9.1M, Liabilities $3.4M; currency **USD**. Chunking, de-duplication, and the
"never invent metrics" contract all held. **Strong feature.**

---

## 6. Document Scoring Engine — verified live

`/analysis` produced a real CSV with model-generated 0.0–1.0 scores across
verification / validation / explainability / persona-suitability, a weighted System
Score, and a coherent one-line remark. When the model returns unparseable output the
engine writes **nulls + an honest "scoring failed" remark** rather than inventing
numbers. **Works and is honest.**

---

## 7. Complete Feature List (verified present)

**Chat & LLM**
- Conversational chat with multi-turn history (capped to last 8 turns)
- 6 selectable providers with automatic, transparent fallback ✅ (4 live)
- 4 selectable personas driving tone/length via a style-guide system prompt
- Strong base system prompt: accuracy-first, no fabricated numbers, educational-not-advice

**Documents**
- Upload PDF / DOCX / PPTX / XLSX / XLS / CSV / TXT + images (PNG/JPG/TIFF/BMP/WEBP/GIF)
- Content-signature (magic-byte) type detection — handles mislabeled files
- Table-structure-preserving extraction (pipe-delimited), header/footer & text-box capture
- OCR fallback for scanned PDFs and images (tesseract, graceful if absent)
- 25 MB upload cap, 200k-char extraction cap, row caps — all flagged inline

**RAG (LightRAG)**
- Per-session isolated indexing + retrieval (mix graph+vector mode)
- Structure-aware chunking; duplicate detection & same-filename replacement
- Retry path for indexing that failed on rate limits; LRU session cache; 7-day sweep
- Web+document **blend** mode (one cited answer from both)

**Web research (Tavily)**
- Iterative (bounded, 2-search) web augmentation with Perplexity-style cited sources
- Recency filtering for time-sensitive queries, trusted-domain boosting, result caching
- Invalid-citation stripping

**Analysis & misc**
- Document scoring engine → CSV; financial-metric extraction → table + CSV download
- Chat history save/load with first-question titles; Streamlit UI with model/persona pickers
- Single-command startup (Streamlit auto-launches the backend); Docker Compose setup

---

## 8. What It Lacks / Weaknesses (verified)

**Operational**
1. **2 of 6 providers are out of credit** (Anthropic 400, Cerebras 402). They're
   selectable in the UI but only work because fallback silently rescues them.
2. **RAG latency 20–28 s per query**, and **web/OpenRouter/Gemini calls 12–15 s** —
   slow for interactive use; no streaming, so the user stares at a spinner.
3. **No reranker configured** in LightRAG (warns every query) — retrieval quality
   is below what the stack can do.

**Code fragility**
4. **`GeminiProvider` crashes on empty/truncated responses** — it uses the
   `response.text` quick accessor, which raises when the model returns no text part
   (e.g. a safety block or a tiny max-tokens budget) instead of degrading gracefully
   like the OpenAI-compatible providers do.
5. **Gemini uses the deprecated `google.generativeai` SDK** (prints an end-of-life
   warning; should move to `google-genai`).
6. **Guardrail can be flattened by format instructions:** asked for a yes/no on
   "put *all* savings into one stock," the assistant replied bare **"No."** — safe
   in direction, but it drops the educational framing / diversification caveat the
   base prompt calls for. The persona/format instruction overrode the "explain
   trade-offs" stance.

**Product gaps**
7. **No authentication** — the FastAPI backend is open, `CORS allow_origins=["*"]`
   with `allow_credentials=True`, and "sessions" are just client-generated UUIDs.
   Fine for local/demo, unsafe to expose.
8. **No data visualization** of analysis/metrics (tables/CSV only).
9. **No test suite** — only ad-hoc `verify_*.py` smoke scripts; several
   (`verify_llm.py`, `verify_slm.py`) still target a **TinyLlama local model that
   the app no longer uses**.

**Docs & config drift**
10. **[project_summary.md](project_summary.md) is stale** — it describes a local
    `TinyLlama-1.1B` SLM run via Transformers; the real app is 100% cloud-API. The
    README is correct; this file contradicts it.
11. **[config/settings.py](config/settings.py) is inconsistent** — `ALLOWED_FILE_TYPES
    = ["csv","pdf","txt"]` and `MAX_UPLOAD_SIZE_MB = 10` don't match the actual
    supported types or the real 25 MB backend cap; `SCORING_WEIGHTS` there differ
    from the weights the scoring engine actually uses, and several constants are dead.

---

## 9. Recommended Priorities

1. Top up or remove the Anthropic/Cerebras entries so the model list reflects reality.
2. Harden `GeminiProvider` (guard `response.text`) and migrate to `google-genai`.
3. Add response **streaming** and/or a **reranker** to cut perceived RAG/web latency.
4. Fix the stale docs/config (items 10–11) and delete the TinyLlama verify scripts.
5. Before any non-local deployment: add auth and lock down CORS.

---

*Artifacts produced during verification: one analysis CSV in
`data/analysis_outputs/`. Verification scripts were run from a scratch dir and are
not committed.*
