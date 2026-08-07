# Evaluation with NotebookLM — Test 2 (Full-Pipeline-Per-Model)

**Date:** 7 August 2026
**Prepared by:** AI-in-Finance project team
**Approach:** Option A — each model builds its **own** RAG index and answers through its **own** full pipeline (index → retrieve → answer). The document is small, so it is indexed in full (no context-truncation caveat).
**Test file:** `sample for test 2.pdf` — "Northwind Sample Holdings, Inc., Q2 FY2026," a quarterly report that contradicts itself in a few places, including a net-income figure that does not reconcile with its own income statement.
**Status:** NotebookLM, Groq, and Mistral complete. **Gemini pending** (Google free-tier daily quota already spent today; scheduled for tomorrow).

---

## Contents

1. [Purpose](#1-purpose)
2. [What I tested and how](#2-what-i-tested-and-how)
3. [How answers were scored](#3-how-answers-were-scored)
4. [Results at a glance](#4-results-at-a-glance)
5. [Question-by-question answers and scores](#5-question-by-question-answers-and-scores)
6. [How each model did](#6-how-each-model-did)
7. [What I found](#7-what-i-found)
8. [Comparison with Test 1](#8-comparison-with-test-1)
9. [Limitations and what's still pending](#9-limitations-and-whats-still-pending)
10. [Conclusion (interim)](#10-conclusion-interim)

---

## 1. Purpose

To measure the app's document Q&A quality on a second document, using **NotebookLM as the
reference**, and to compare the project's models. This document contradicts itself in a few
spots — including a net income that does not reconcile with its own income statement — which
tests whether a system notices problems or just answers confidently. Gemini will be added
once its quota resets.

---

## 2. What I tested and how

Each model was run in **Option A** style: given the document, it **built its own index**
(knowledge graph + vector store), then answered the **same 12 questions** through its own
retrieval and answering — exactly how the app would behave if configured to use that model
end-to-end.

| Source | Status |
|--------|--------|
| **NotebookLM** | Complete — the reference. |
| **Groq (full RAG)** | Complete — this is what the app ships today. |
| **Mistral (full RAG)** | Complete. |
| **Gemini (full RAG)** | Pending — deferred to tomorrow (daily quota exhausted). |

The 12 questions cover **Facts** (Q1–Q3), **Calculations** (Q4–Q6), **Contradictions**
(Q7–Q9), and **Traps** where the answer isn't in the document (Q10–Q12).

---

## 3. How answers were scored

| Rating | Symbol | Meaning |
|--------|:---:|---------|
| Right | ✔ | Correct. For contradiction questions, it flagged the conflict / gave the authoritative figure. |
| Partial | ◐ | Close but flawed — right figure without flagging the conflict, spotted the issue but didn't fully resolve it, or correct content spoiled by a defect (e.g. wrong language). |
| Wrong | ✘ | Incorrect, didn't answer, or gave the misleading figure. |

Score = Right 100%, Partial 50%, Wrong 0%, averaged over the 12 questions.

---

## 4. Results at a glance

**Legend:** ✔ = Right · ◐ = Partial · ✘ = Wrong · — = pending

| # | Question | NotebookLM | Groq (full RAG) | Mistral (full RAG) | Gemini (full RAG) |
|---|----------|:---:|:---:|:---:|:---:|
| 1 | Q2 revenue | ✔ | ✔ | ✔ | — |
| 2 | Total assets | ✔ | ✔ | ✔ | — |
| 3 | Top segment | ✔ | ✔ | ✔ | — |
| 4 | Net change in cash | ✔ | ✔ | ✔ | — |
| 5 | Effective tax rate | ✔ | ✔ | ✘ | — |
| 6 | Net income change | ✔ | ✔ | ✔ | — |
| 7 | Operating margin (conflict) | ✔ | ✘ | ✘ | — |
| 8 | Operating expenses (conflict) | ✔ | ✘ | ✘ | — |
| 9 | Net income reconciliation (conflict) | ◐ | ◐ | ✘ | — |
| 10 | Dividend (trap) | ✔ | ✔ | ✔ | — |
| 11 | EPS (trap) | ✔ | ✔ | ✔ | — |
| 12 | Q3 revenue (trap) | ✔ | ✔ | ◐ | — |
| | **Right (✔)** | 11 | 9 | 7 | — |
| | **Partial (◐)** | 1 | 1 | 1 | — |
| | **Wrong (✘)** | 0 | 2 | 4 | — |
| | **Score** | **95.8%** | **79.2%** | **62.5%** | — |

---

## 5. Question-by-question answers and scores

Each answer is quoted from the actual output and rated individually. Ground-truth figures are
taken from the detailed tables in the source document.

### Facts (Q1–Q3)

**Q1. Total revenue in Q2 FY2026?** *(Correct: $4,820,000)*
- NotebookLM — "$4,820,000." — **✔**
- Groq — "$4,820,000." — **✔**
- Mistral — "$4,820,000; an 8.4% increase over Q1's $4,447,000." — **✔**

**Q2. Total assets as of Jun 30, 2026?** *(Correct: $14,510,000)*
- NotebookLM — "$14,510,000." — **✔**
- Groq — "$14,510,000." — **✔**
- Mistral — "$14,510,000." — **✔**

**Q3. Highest-revenue segment in Q2, and amount?** *(Correct: Product Sales, $3,102,000)*
- NotebookLM — "Product Sales, $3,102,000 (64.4% of total revenue)." — **✔**
- Groq — "Product Sales, $3,102,000 (64.4%)." — **✔**
- Mistral — "Product Sales, $3,102,000 (64.4%)." — **✔**

### Calculations (Q4–Q6)

**Q4. Net change in cash during Q2?** *(Correct: +$730,000)*
- NotebookLM — "$730,000 during the quarter." — **✔**
- Groq — "$730,000." — **✔**
- Mistral — "$730,000." — **✔**

**Q5. Effective tax rate in Q2?** *(Correct: ≈30.1% = 148,000 ÷ 492,500)*
- NotebookLM — "≈30.05% ($148,000 ÷ $492,500)." — **✔**
- Groq — "($148,000 / $492,500) × 100 ≈ 30.0%." — **✔**
- Mistral — "3.1% … based on $148,000 tax on $492,500 pre-tax income." — **✘** *(3.1% is tax as a % of revenue; the operands it cites equal 30% — the same error as Test 1)*

**Q6. Change in net income from Q1 to Q2?** *(Correct: +$177,200, $1,015,300 → $1,192,500)*
- NotebookLM — "+$177,200 ($1,015,300 → $1,192,500)." — **✔**
- Groq — "$1,192,500 − $1,015,300 = $177,200." — **✔**
- Mistral — "+$177,200, a 17.5% increase." — **✔**

### Contradictions (Q7–Q9)

**Q7. Operating margin in Q2?** *(Authoritative: 9.4% = $452,000 ÷ $4,820,000; the Exec Summary's 34.7% is the misleading figure)*
- NotebookLM — "The Executive Summary states 34.7%. Note: the detailed income statement shows a 9.4% operating-income margin; the 34.7% is based on the $3,145,000 operating-expense figure in the high-level metrics." — **✔** *(flagged the conflict and explained both figures)*
- Groq — "34.7%, based on operating expenses of $3,145,000." — **✘** *(the misleading figure; no conflict flagged)*
- Mistral — "34.7% — Operating Income $452,000 / Total Revenue $4,820,000 ≈ 34.7%." — **✘** *(states 34.7% but its own division equals 9.4%; internally contradictory)*

**Q8. Total operating expenses in Q2?** *(Authoritative: $2,445,000, detailed line items; the summary's $3,145,000 is the outlier)*
- NotebookLM — "The summary table lists $3,145,000. However, the detailed breakdown (S&M, R&D, G&A) totals $2,445,000." — **✔** *(flagged the conflict and gave both)*
- Groq — "$3,145,000." — **✘** *(the non-authoritative summary figure; no conflict flagged)*
- Mistral — "$3,145,000." — **✘** *(same)*

**Q9. Net income in Q2, and does it reconcile with the income statement?** *(Reported $1,192,500, but Income Before Tax $492,500 − Tax $148,000 = $344,500 — it does NOT reconcile; the "rounding adjustment" note cannot explain an ~$848k gap)*
- NotebookLM — "$1,192,500. The report notes this figure reflects a 'small rounding adjustment for illustrative purposes'." — **◐** *(gave the figure and surfaced the document's caveat, but **accepted** the rounding explanation and did not catch that a "small rounding adjustment" cannot account for the ~$848k discrepancy)*
- Groq — "$1,192,500. [Walks the P&L to Income Before Tax $492,500.] …we cannot reconcile it with the income statement using the information provided." — **◐** *(correctly recognised the reported net income does not reconcile — arguably the strongest answer here — but framed it as "missing info" rather than naming the implied $344,500)*
- Mistral — "$1,192,500 … after accounting for all revenues, expenses, and taxes … further supports the reconciliation." — **✘** *(wrongly asserts it reconciles)*

### Traps (Q10–Q12)

**Q10. Dividend per share declared?** *(Not in the document)*
- NotebookLM — "The sources do not contain information regarding declared dividends." — **✔**
- Groq — "Not stated; no dividend/per-share information." — **✔**
- Mistral — "Not enough information; no dividend details." — **✔**

**Q11. Earnings per share (EPS)?** *(Not in the document — no share count)*
- NotebookLM — "The sources do not contain information regarding earnings per share." — **✔**
- Groq — "Cannot calculate; shares outstanding not provided." — **✔**
- Mistral — "Not enough information; no EPS data." — **✔**

**Q12. Q3 FY2026 total revenue?** *(Not in the document — only Q1 and Q2 given)*
- NotebookLM — "Not available; the report only covers up to Q2 FY2026." — **✔**
- Groq — "Not enough information; only Q1 and Q2 are provided." — **✔**
- Mistral — *(answered in German)* "Ich habe nicht genug Informationen … nur Q1 FY2026 und Q2 FY2026." — **◐** *(correct content, but replied in German — a defect)*

---

## 6. How each model did

**NotebookLM — 95.8% (11 / 1 / 0).** The reference, and the strongest — but **not perfect on
Test 2**. It handled the operating-margin and operating-expenses conflicts (Q7, Q8) exactly
right, presenting both figures and explaining where each comes from. Its one slip was the
**reconciliation question (Q9)**: it accepted the document's "small rounding adjustment" note
instead of noticing the net income cannot foot (~$848k off). No hallucinations.

**Groq (full RAG) — 79.2% (9 / 1 / 2).** The app as it ships. Perfect on facts,
calculations, and traps, with no hallucinations. Notably, on **Q9 it arguably beat the
reference** — it worked the income statement down to Income Before Tax $492,500 and concluded
the reported net income "cannot be reconciled," rather than accepting the rounding note. Its
weaknesses are the other two contradictions (Q7 gave 34.7%; Q8 gave $3,145,000), where it
returned a single figure without flagging the disagreement.

**Mistral (full RAG) — 62.5% (7 / 1 / 4).** Strong on facts and traps, and fast, but it
accumulated errors: it repeated the **"3.1%" tax-rate mistake** from Test 1 (Q5), stated
**34.7%** on Q7 while its own arithmetic equals 9.4% (internally contradictory), gave the
non-authoritative operating-expenses figure (Q8), and **wrongly claimed the net income
reconciles** (Q9). It also answered Q12 **in German** — correct content, wrong language.

---

## 7. What I found

1. **The reconciliation trap (Q9) was the hardest — it caught even NotebookLM.** Only Groq
   flagged that the reported net income doesn't reconcile; NotebookLM accepted the "rounding
   adjustment" hand-wave, and Mistral claimed it reconciles. This is the one place the
   shipping app **outperformed the reference**.
2. **NotebookLM handled the other two contradictions cleanly** (Q7, Q8) — presenting both the
   summary and detailed figures and explaining the discrepancy. The local models did not.
3. **The local models' contradiction blind spot persists** — Groq and Mistral both returned
   the Executive-Summary figures (34.7%, $3,145,000) without flagging the conflict, consistent
   with the finding that the retrieval/knowledge-graph stage surfaces one figure and buries
   the disagreement.
4. **Mistral has recurring defects:** the "% of revenue vs effective tax rate" confusion (Q5)
   and answering in German (Q12) both recurred from Test 1.
5. **No hallucinations** — every source correctly abstained on all three traps.

---

## 8. Comparison with Test 1

| Model | Test 1 | Test 2 |
|-------|:---:|:---:|
| NotebookLM | 100% | **95.8%** |
| Groq (full RAG) | 79.2% | **79.2%** |
| Mistral (full RAG) | 70.8% | **62.5%** |

Groq is **consistent** across both documents (79.2%). NotebookLM slipped from a perfect score
because Test 2's reconciliation trap is subtler than any single-figure conflict in Test 1.
Mistral dropped, mainly due to the harder reconciliation question and its recurring tax-rate
and language defects.

---

## 9. Limitations and what's still pending

- **Gemini not yet run** — Google's free-tier daily quota (20 requests) was already spent on
  Test 1 today. Gemini's Test 2 column will be filled after the quota resets. Note: tomorrow's
  single-day quota cannot cover **both** finishing Test 1's Gemini and a full Test 2 Gemini run
  — these need to be spread across days (or a paid quota).
- **Single document, single pass.** One attempt per question.
- **Some judgement in scoring**, applied consistently (e.g. Q9 "recognised non-reconciliation"
  as Partial for Groq and "surfaced the caveat but accepted it" as Partial for NotebookLM;
  German answers as a scored defect).

---

## 10. Conclusion (interim)

On Test 2, **NotebookLM leads at 95.8%**, the shipping **Groq pipeline holds at 79.2%**, and
**Mistral trails at 62.5%**. The most interesting result is the **reconciliation trap (Q9)**:
it defeated even NotebookLM, and the shipping app was the only source to flag that the
document's net income doesn't add up — a reminder that "reference-grade" is not infallible on
subtle internal-consistency checks. The local models' persistent weakness remains **surfacing
the document's single-figure contradictions** (operating margin, operating expenses), which
Test 2 again ties to the retrieval stage returning one figure. The comparison completes once
**Gemini** is added tomorrow.
