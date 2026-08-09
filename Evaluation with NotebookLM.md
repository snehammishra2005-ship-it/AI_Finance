# Evaluation with NotebookLM — Summary

**Date:** 8 August 2026
**What this is:** a summary of how the AI-in-Finance app's document Q&A was evaluated against NotebookLM, and what the results say so far (Test 1 complete, Test 2 mostly complete, Test 3 pending).

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

---

## 3. Conclusions so far

1. **The app is accurate and honest on the basics.** Across both tests, the shipping Groq
   pipeline matched the reference on facts, calculations, and traps — and **made nothing up**
   (every model correctly said "not stated" on all the trap questions).
2. **Groq is consistent** — **79.2% on both tests** — a stable, dependable default.
3. **The weak spot is contradictions.** The app's local models (Groq, Mistral) tend to hand
   back one figure without noticing when the document disagrees with itself. This traces to
   the retrieval step surfacing a single figure and burying the conflict.
4. **Gemini is the strongest of the app's models** — 91.7% on Test 1 and a perfect **100% on
   Test 2** (Option B). It reliably flags contradictions and gives both figures. Switching the
   document model to Gemini is the clearest quality lever (the app is Groq-only for documents
   today).
5. **The reference isn't infallible.** Test 2's hardest question — a net income that doesn't
   reconcile with its own income statement — **caught even NotebookLM** (and Mistral wrongly said
   it reconciles). Only **Gemini fully caught it**, and Groq partly did. "Reference-grade" still
   misses subtle internal-consistency problems.
6. **Persona + RAG now work together.** As part of this work, the app was upgraded so a
   grounded document answer is also **worded for the reader's finance level** (Student, MBA,
   Senior Citizen, …) — with a hard guardrail that never lets the styling change a number.
   Verified working on both Groq and Gemini: the same facts come out as a short, plain,
   analogy-led answer for a beginner and a detailed, technical one for an expert, with every
   figure identical.

**Bottom line:** the app (on Groq) is a reliable, honest document assistant that's strong on
facts and safe on the unknown, with one real gap — spotting a document's self-contradictions —
that a stronger model (Gemini) largely closes.

---

## Note — Test 3 is still remaining

**Test 3 has not been run yet, and it is blocked by Gemini's free-tier quota limit of
20 requests/day.** A full per-model Gemini run is request-heavy, and **Test 3 will need more
than 40 requests** to complete. Under the 20-per-day cap, that means it will take **more than
2–3 days** to finish. Until either the quota is spread across several days or a paid Gemini
quota is added, Test 3 remains pending.
