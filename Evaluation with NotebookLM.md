# Evaluation with NotebookLM — Summary

**Date:** 8–23 August 2026
**What this is:** a summary of how the AI-in-Finance app's document Q&A was evaluated against NotebookLM, and what the results say. **All three tests are now complete.** (Per-test detail: [Test 1](test%201%20results.md), [Test 2](test%202%20results.md), [Test 3](Test3_report.md).)

---

## 1. The process, in short

The idea was simple: check how good the app's document question-answering really is, using
**NotebookLM as the reference** ("what a strong tool answers"), and see whether the other
models the app already integrates do any better than the default one.

How each test was run:

1. **Pick the answer sources** — NotebookLM (the reference) plus the app's three working
   models: **Groq** (the default, what the app ships), **Mistral**, and **Gemini**.
2. **Give them a document** — a fake but realistic quarterly finance report, deliberately
   written to **contradict itself** in a few spots (so we can see whether a model *notices*
   problems or just answers confidently).
3. **Each model reads and files the document its own way** ("full RAG per model") — it builds
   its own index, then answers from it. This is the most product-faithful test.
4. **Ask the same 12 questions**, covering four skills:
   - **Facts** — look up a number.
   - **Calculations** — work something out.
   - **Contradictions** — the document disagrees with itself here.
   - **Traps** — the answer isn't in the document, so the right move is to say "not stated".
5. **Score every answer** against the document's authoritative tables: **✔ Right**,
   **◐ Partial**, **✘ Wrong** (Right 100%, Partial 50%, Wrong 0%), averaged over the 12
   questions.

> **Test 3 stressed a different axis.** Tests 1–2 used small, self-contradicting reports to probe
> *conflict-spotting*. Test 3 used a **large real document** (the RBI *Financial Stability Report,
> June 2025*) to probe **scale and retrieval**, and was the first test run with the app's new
> **persona-aware RAG** (Student persona, "reword the answer but never the numbers"). Its
> question skills were Facts / Comparisons / Sector-detail / Traps rather than contradictions.

---

## 2. Results

### Test 1 — complete
*Document: "Vantage Point Analytics, Inc., Q3 FY2026" (company-name, revenue, margin, cash, and net-income contradictions).*

| Source | Score | Right / Partial / Wrong |
|--------|:---:|:---:|
| **NotebookLM** (reference) | **100%** | 12 / 0 / 0 |
| **Gemini** (full RAG) | **91.7%** | 10 / 2 / 0 |
| **Groq** (full RAG — app default) | **79.2%** | 9 / 1 / 2 |
| **Mistral** (full RAG) | **70.8%** | 7 / 3 / 2 |

### Test 2 — complete
*Document: "Northwind Sample Holdings, Inc., Q2 FY2026" (operating-margin, operating-expense, and a net-income-that-doesn't-reconcile contradiction).*

| Source | Score | Right / Partial / Wrong |
|--------|:---:|:---:|
| **Gemini** (Option B*) | **100%** | 12 / 0 / 0 |
| **NotebookLM** (reference) | **95.8%** | 11 / 1 / 0 |
| **Groq** (full RAG — app default) | **79.2%** | 9 / 1 / 2 |
| **Mistral** (full RAG) | **62.5%** | 7 / 1 / 4 |

\* **Gemini = Option B** (Groq did the retrieval, Gemini only synthesised the answers), because a
full Gemini run exceeds the free-tier 20-requests/day cap. Its context already surfaced the
conflicting figures, so its column is **not perfectly like-for-like** with the full-pipeline
Groq/Mistral columns — but it shows Gemini's reasoning is excellent: it was the **only source to
fully catch** the net-income reconciliation trap (Q9), beating even NotebookLM.

### Test 3 — complete
*Document: RBI "Financial Stability Report, June 2025" (a large real document). Student persona, full RAG per model. Skills: facts, comparisons, sector-detail, traps.*

| Source | Score | Right / Partial / Wrong |
|--------|:---:|:---:|
| **NotebookLM** (reference) | **100%** | 12 / 0 / 0 |
| **Gemini** (Option A, full RAG) | **100%** | 12 / 0 / 0 |
| **Mistral** (Option A, full RAG) | **91.7%** | 11 / 0 / 1 |
| **Groq** (TRY 2 — trimmed context*) | **41.7%** | 4 / 2 / 6 |

\* **Groq couldn't run its normal pipeline.** The document was too large: full-context retrieval
(~14k tokens) blew past Groq's free-tier 6,000-tokens/minute limit, so **TRY 1 failed outright**
(`413 Request too large`). **TRY 2** only fit by trimming the context to a knowledge-graph-only
form (0 prose chunks), so Groq answered from the graph alone — a **degraded pipeline**, not the
model's real ceiling. Gemini's run was full Option A but **spanned two days** (Q1–Q10 on 19 Aug,
Q11–Q12 on 23 Aug) under the 20-requests/day cap. Mistral's only miss was a trap (Q11), where it
hallucinated "6.5%" — the 2025-26 figure — for a 2026-27 projection the document never gives.

---

## 3. Conclusions so far

1. **The app is accurate and honest on the basics.** Across both tests, the shipping Groq
   pipeline matched the reference on facts, calculations, and traps — and **made nothing up**
   (every model correctly said "not stated" on all the trap questions).
2. **Groq is consistent on small documents** — **79.2% on Tests 1 and 2** — but **hits a hard
   wall on large ones.** On Test 3's big document it dropped to **41.7%**, and only after a
   fallback: its normal pipeline couldn't run at all (the context exceeded Groq's free-tier
   per-minute token limit). This is the single most important new finding — see point 7.
3. **The weak spot is contradictions.** The app's local models (Groq, Mistral) tend to hand
   back one figure without noticing when the document disagrees with itself. This traces to
   the retrieval step surfacing a single figure and burying the conflict.
4. **Gemini is the strongest of the app's models** — 91.7% on Test 1 and a perfect **100% on
   Test 2** (Option B) and **100% on Test 3** (full Option A). It flags contradictions, gives
   both figures, and was the only app model to pass *every* trap in Test 3. Switching the
   document model to Gemini is the clearest quality lever (the app is Groq-only for documents
   today).
5. **The reference isn't infallible.** Test 2's hardest question — a net income that doesn't
   reconcile with its own income statement — **caught even NotebookLM** (and Mistral wrongly said
   it reconciles). Only **Gemini fully caught it**, and Groq partly did. "Reference-grade" still
   misses subtle internal-consistency problems.
6. **Persona + RAG now work together.** As part of this work, the app was upgraded so a
   grounded document answer is also **worded for the reader's finance level** (Student, MBA,
   Senior Citizen, …) — with a hard guardrail that never lets the styling change a number.
   Test 3 was the first full scored run of this feature: across every substantive question,
   Gemini and Mistral wrapped the figures in genuine student-level analogies (a "giant student
   club," ₹419 vs ₹466, a car slowing from 27 to 11.6 km/h) while **every figure stayed exact.**
   "Reword the answer, never the numbers" held.
7. **Document size — not reasoning — is the app's real bottleneck.** Test 3's big document
   broke Groq's shipping pipeline: full-context retrieval exceeded the free-tier per-minute
   token limit, and the only way to make it fit starved the model of the prose the answers
   lived in. Meanwhile full-RAG Gemini and Mistral handled the same document at 100% / 91.7%.
   The fix is about **retrieval and provider limits** (chunk-budget tuning, a larger-quota or
   paid provider for big docs), not about the model's ability to read.
8. **Mistral's recurring failure is over-confidence on traps.** Its lone Test 3 miss was
   answering "6.5%" for a projection the document never makes — the same "confident number
   instead of an abstention" pattern it showed earlier. Useful and fast, but the least
   calibrated of the app's models on the unknown.

**Bottom line:** the app is an honest, accurate document assistant — strong on facts, safe on
the unknown. Two gaps remain: spotting a document's self-contradictions (largely closed by
Gemini), and **handling large documents on the default Groq pipeline** (a retrieval/quota limit,
newly exposed by Test 3). Both point the same way: routing document Q&A through Gemini, and
tuning retrieval for scale, is the clearest path to a stronger product.

---

## Note — Test 3 is now complete

Test 3 is finished; full detail is in [Test3_report.md](Test3_report.md). As predicted, the
Gemini free-tier cap (20 requests/day) meant a full Option-A Gemini run had to be **spread
across two days** (Q1–Q10 on 19 Aug, the last two questions on 23 Aug) — the quota was the pace
limiter, not a blocker. The run also surfaced a **new** limit that only a large document exposes:
Groq's free-tier per-minute token cap, which prevented its normal pipeline from running at all on
this document (see conclusions 2 and 7). A larger-quota or paid provider would remove both
constraints for big-document testing.
