# AI in Finance — Verified Output-Quality Report (Updated)

**Date:** 2026-08-02 (post-fix revision)
**Method:** Every claim was verified by running the project's own code against
the live APIs (repo `.env` keys, project `venv`) — not read from docs. This
revision reflects the state **after** the fixes for streaming, the Gemini SDK,
the advice guardrail, CORS, the reranker warning, config drift, and the new
test suite. Streaming and the analysis chart were additionally verified in a
real browser session.

> **Update (Aug 2026) — changes since this 2026-08-02 probe:** Groq retired
> `llama-3.1-8b-instant`; the default is now **`openai/gpt-oss-20b`**
> (`reasoning_effort="low"`). Since this report, the app also gained **per-user JWT
> auth** and **persona-aware RAG** (grounded answers reworded for the reader, figures
> held exact), and the document Q&A was evaluated against NotebookLM across three tests
> (see `Evaluation with NotebookLM.md`). The point-in-time probe results below are
> preserved as-is.

---

## 1. Verdict

Core output quality is **good and now more robust** than at the first review.
Chat is accurate and streams token-by-token, document Q&A (RAG) retrieves and
cites correctly and refuses out-of-document questions, metric extraction is
precise, and the advice guardrail can no longer be flattened to a bare yes/no.
The remaining issues are **operational** (three of six model providers are out
of or low on API credit) and **inherent latency** on RAG/web answers — not core
correctness.

| Area | Status | Evidence |
|------|--------|----------|
| Chat quality | ✅ Good | Live, §3 |
| Chat streaming | ✅ Working (token-by-token) | Live + browser, §4 |
| Advice guardrail | ✅ Enforced (deterministic backstop) | Live + unit tests, §3 |
| Provider routing + fallback | ✅ Works, rescues dead providers | Live, §2 |
| RAG document Q&A | ✅ Accurate, cited, no hallucination | Live, §5 |
| RAG reranker warning | ✅ Silenced | Live log, §5 |
| Metric extraction | ✅ Precise (5/5) | Live, §6 |
| Scoring engine | ✅ Works, honest fallback | Live, §6 |
| Gemini provider | ✅ Fixed (was crashing) | Live, §2 |
| CORS posture | ✅ Restricted | Live, §7 |
| Test suite | ✅ 55 passing, offline | Live, §8 |
| Provider availability | ⚠️ 3/6 solid; 1 low-credit; 2 out of credit | Live, §2 |
| RAG/web latency | ⚠️ Slow (inherent) | Live, §5 |

---

## 2. LLM Providers — verified live (direct call, no fallback)

Fresh probe at 23:45 on 2026-08-02:

| Provider (model) | Result | Latency | Notes |
|---|---|---|---|
| **Groq** — Llama 3.1 8B Instant _(now `gpt-oss-20b`; see Update)_ | ✅ Working | ~0.6 s | Default; fastest, most reliable |
| **Google** — Gemini 3 Flash | ✅ Working | ~8.4 s | **Now fixed** — migrated to `google-genai`, thinking disabled, empty-response guarded. Previously crashed on the old SDK. |
| **Mistral** — Mistral Small | ✅ Working | ~0.7 s | Works, fast |
| **OpenRouter** — GPT-5.5 | ⚠️ Low credit | — | Returns empty/`402` — account is nearly out of credit (observed "can only afford 214 tokens" on a 512-token request) |
| **Anthropic** — Claude 3 Haiku | ❌ Out of credit | — | `400 — credit balance too low` |
| **Cerebras** — GPT-OSS 120B | ❌ Out of credit | — | `402 — payment required` |

**Change since last report:** Gemini moved from *fragile/crashing* to *working*.
OpenRouter moved from *working* to *low-credit/degraded*. Groq, Mistral, Anthropic,
and Cerebras are unchanged.

**Resilience (verified):** the fallback chain still transparently rescues a
request routed to a dead/degraded provider — a chat aimed at Anthropic/Cerebras/
OpenRouter is answered by the next configured provider. A single provider being
down does not break chat.

---

## 3. Chat Output Quality & Guardrail — verified live

**General quality:** answers lead with the point, use clean Markdown, define
terms, and honor persona/length instructions. Verified probes:
- *"What is inflation?"* → accurate, plain-language, correctly bolded, 2 sentences.
- *"Exact closing price of Apple on 2025-07-14?"* → correctly **refused**, cited
  lack of real-time data, no fabricated number.

**Advice guardrail (the item that previously failed):** at the first review,
*"Should I put all my savings into Tesla? answer only yes or no"* returned a bare
**"No."**, dropping the required educational framing. Now, verified live, the same
forced-format question returns:

> No.
>
> This is a personal financial decision with real trade-offs — and putting a
> large share of your money into a single asset concentrates your risk. Weigh it
> against your own goals … consider consulting a licensed financial advisor …

This is enforced by a **deterministic backstop** (`advice_safety_note`) that
appends the framing when a first-person buy/sell/invest question collapses to a
bare yes/no — so it holds regardless of how strictly the model is told to be
terse. A general factual question that happens to get a short answer is **not**
affected (verified: *"Is a higher credit score better?"* → normal answer, no
appended note). Covered by 7 dedicated unit tests.

---

## 4. Chat Streaming — verified live + in browser (new capability)

Plain chat now **streams token-by-token** instead of blocking on a spinner:
- **HTTP** (`POST /chat/stream`): a 3-tip answer arrived as **76 incremental
  chunks**; multi-byte currency characters (₹) survived the chunk boundaries
  (incremental UTF-8 decode).
- **Browser** (isolated Streamlit instance): submitting *"Give me 3 quick tips
  to start budgeting"* rendered the assistant reply streaming into the bubble
  live, with correct Student-persona formatting and the model caption.

Web/RAG/blend modes intentionally remain on the non-streamed JSON path (they need
citation/source post-processing). Streaming keeps the same provider-fallback
behavior *before* the first token is emitted.

---

## 5. RAG / Document Q&A — verified live

Ingest → query on a synthetic report:

| Question | Answer | Correct? |
|---|---|---|
| Q2 revenue & growth | "$12.4M … 27% increase over Q2 2024 ($9.76M)" + citation | ✅ |
| Dividend & date | "$0.15 per share, payable September 2025" | ✅ |
| New distribution centers | "Texas and Ohio" | ✅ |
| Employee headcount (**not in doc**) | "the context does not contain any information…" | ✅ (no hallucination) |

Per-session isolation, structure-aware chunking, table preservation, and
duplicate/replace handling are all present and exercised. A follow-up live query
confirmed the **reranker warning is gone** (0 occurrences in the backend log)
while retrieval still uses graph+vector recall and returns correct, cited answers.

**Latency (verified):** RAG answers take ~20–28 s (multi-step retrieval + Groq
synthesis on the free tier); web-augmented answers 12–15 s. This is inherent to
the stack/tier, not a defect in the logic.

---

## 6. Metric Extraction & Scoring — verified live

- **Metric extraction:** from a 5-fact sample, returned **5/5 metrics** correctly
  with currency (USD) and periods (Revenue, Net profit, Operating margin, Total
  assets, Liabilities). Chunking, de-duplication, and the "never invent metrics"
  contract all held.
- **Scoring engine:** produced a real CSV with model-generated 0–1 scores across
  verification / validation / explainability / persona-suitability plus a weighted
  System Score and a coherent remark. On unparseable model output it writes nulls
  + an honest "scoring failed" remark rather than inventing numbers. The analysis
  view now renders a **score bar chart** (chart data-prep verified against a real
  CSV).

---

## 7. Security Posture — verified live

- **CORS is now restricted:** a preflight from `http://localhost:8501` is allowed;
  a preflight from `https://evil.example` is **rejected** (no allow-origin header).
  Overridable via `CORS_ALLOW_ORIGINS`. This replaces the previous unsafe
  `allow_origins=["*"]` + `allow_credentials=True` combination.
- **Still no authentication:** the backend remains open and "sessions" are
  client-generated UUIDs — acceptable for local/single-user use, not for a shared
  deployment.

---

## 8. Testing — verified live

An offline unit-test suite now exists under `tests/` — **55 tests, all passing**
via `python -m unittest discover -s tests`, with no network calls or API keys
required. Coverage: citation stripping, web/blend prompt assembly, score parsing
(clamping, prose tolerance, failure paths), metric parsing, file-type magic-byte
detection, table formatting, extraction thresholds, CSV parsing, persona loading,
history-title derivation, the advice-guard backstop, and settings/​backend
consistency. The dead TinyLlama `verify_llm.py` and the broken `verify_backend.py`
were removed.

---

## 9. Remaining Limitations (verified, observational)

1. **Provider credit:** only Groq, Gemini, and Mistral are fully working;
   OpenRouter is nearly out of credit and Anthropic/Cerebras are out. They stay
   selectable in the UI and are covered by fallback, but their own direct calls
   fail.
2. **RAG/web latency:** ~20–28 s (RAG) and ~12–15 s (web) per answer, inherent to
   free-tier multi-step retrieval + synthesis; streaming is not applied to these
   modes.
3. **No authentication:** backend is open; intended for local use only.
4. **No reranker model:** the warning is silenced and recall is unaffected for
   the current corpus sizes, but no learned reranking is performed.
5. **Metric visualization:** metrics are shown as a table (mixed units — $ and %
   — make a single-axis chart misleading); only the 0–1 analysis scores are
   charted.

---

*Verification artifacts created during this review were cleaned up; the analysis
CSV(s) and RAG test sessions generated for the live checks were removed.*
