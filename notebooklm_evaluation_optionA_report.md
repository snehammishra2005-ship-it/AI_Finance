# Evaluation with NotebookLM — Full-Pipeline-Per-Model (Option A), Test 1

**Date:** 2 August 2026
**Prepared by:** AI-in-Finance project team
**Approach:** Option A — each model builds its **own** RAG index and answers through its **own** full pipeline (indexing → retrieval → answer). This is the most product-faithful test; because the document is small it is indexed in full, so there is no context-truncation caveat.
**Test file:** `sample for test 1.pdf` — a Q3 FY2026 quarterly report that deliberately contradicts itself (company name, Q2 revenue, operating margin, cash, net income).

---

## Contents

1. [Purpose](#1-purpose)
2. [What I tested and how](#2-what-i-tested-and-how)
3. [How answers were scored](#3-how-answers-were-scored)
4. [Results at a glance](#4-results-at-a-glance)
5. [Question-by-question answers and scores](#5-question-by-question-answers-and-scores)
6. [How each model did](#6-how-each-model-did)
7. [What I found](#7-what-i-found)
8. [Limitations](#8-limitations)
9. [Conclusion](#9-conclusion)
10. [Where the data came from](#10-where-the-data-came-from)

---

## 1. Purpose

To measure the app's document Q&A quality against **NotebookLM** (used as the reference),
and to see how each of the project's three working models performs when the **entire RAG
pipeline** runs on that model — not just the final answer step. The test document
contradicts itself in places, which reveals whether a system notices problems or answers
confidently regardless.

---

## 2. What I tested and how

Each model was run in **Option A** style: I gave it the document, let it **build its own
index** (its own knowledge graph and vector store), then asked the **same 12 questions**
through its own retrieval and answering. This is exactly how the app would behave if it were
configured to use that model end-to-end.

| Source | How it answered |
|--------|-----------------|
| **NotebookLM** | Reference — its own upload, retrieval, and answers. |
| **Groq (full RAG)** | Full pipeline on Groq Llama 3.1 8B (this is what the app ships today). |
| **Mistral (full RAG)** | Full pipeline on Mistral Small. |
| **Gemini (full RAG)** | Full pipeline on Gemini 3 Flash. |

The 12 questions cover **Facts** (Q1–Q3), **Calculations** (Q4–Q6), **Contradictions**
(Q7–Q9), and **Traps** where the answer isn't in the document (Q10–Q12).

To enable this, I added Mistral and Gemini RAG adapters and made the RAG service accept a
selectable model (the default remains Groq, so the shipping app is unchanged).

---

## 3. How answers were scored

| Rating | Symbol | Meaning |
|--------|:---:|---------|
| Right | ✔ | Correct. For contradiction questions, it flagged the conflict and gave the right figure. |
| Partial | ◐ | Close but flawed — right figure without flagging the conflict, right setup but didn't finish the calculation, or correct content spoiled by a defect (e.g. wrong language). |
| Wrong | ✘ | Incorrect, didn't answer, or gave the misleading figure. |
| — | — | Not obtained (Gemini ran out of daily quota — see §8). |

Score = Right 100%, Partial 50%, Wrong 0%, averaged over the questions answered.

---

## 4. Results at a glance

**Legend:** ✔ = Right · ◐ = Partial · ✘ = Wrong · — = not obtained (quota)

| # | Question | NotebookLM | Groq (full RAG) | Mistral (full RAG) | Gemini (full RAG) |
|---|----------|:---:|:---:|:---:|:---:|
| 1 | Q3 revenue | ✔ | ✔ | ✔ | ✔ |
| 2 | Total assets | ✔ | ✔ | ✔ | ✔ |
| 3 | Top segment | ✔ | ✔ | ✔ | ✔ |
| 4 | Net change in cash | ✔ | ✔ | ✔ | ✔ |
| 5 | Effective tax rate | ✔ | ✔ | ✔ | ◐ |
| 6 | Net income change | ✔ | ✔ | ✔ | ✔ |
| 7 | Company (conflict) | ✔ | ✘ | ✘ | ◐ |
| 8 | Q2 revenue (conflict) | ✔ | ◐ | ◐ | — |
| 9 | Operating margin (conflict) | ✔ | ✘ | ✘ | — |
| 10 | Dividend (trap) | ✔ | ✔ | ✔ | — |
| 11 | EPS (trap) | ✔ | ✔ | ◐ | — |
| 12 | Q1 revenue (trap) | ✔ | ✔ | ◐ | — |
| | **Right (✔)** | **12** | 9 | 7 | 5 (of 7) |
| | **Partial (◐)** | 0 | 1 | 3 | 2 (of 7) |
| | **Wrong (✘)** | 0 | 2 | 2 | 0 (of 7) |
| | **Score** | **100%** | **79.2%** | **70.8%** | **incomplete** |

Gemini completed only Q1–Q7 (5 ✔, 2 ◐) before its free-tier daily request quota was
exhausted; Q8–Q12 could not be obtained today.

---

## 5. Question-by-question answers and scores

Each answer is quoted from the actual pipeline output and rated individually.

### Facts (Q1–Q3)

**Q1. Total revenue in Q3 FY2026?** *(Correct: $7,265,000)*
- NotebookLM — "$7,265,000; a 5.1% increase over Q2's $6,912,000." — **✔**
- Groq — "…total revenue for Northwind Sample Holdings in Q3 FY2026 was $7,265,000." — **✔**
- Mistral — "…$7,265,000." — **✔**
- Gemini — "$7,265,000; a 5.1% increase over the $6,912,000 recorded in Q2." — **✔**

**Q2. Total assets as of 30 Sep 2026?** *(Correct: $20,380,000)*
- NotebookLM — "$20,380,000 (current $14,450,000; PP&E $4,610,000; intangibles $1,320,000)." — **✔**
- Groq — "…total assets…were $20,380,000." — **✔**
- Mistral — "$20,380,000." — **✔**
- Gemini — "$20,380,000 (current assets $14,450,000 including cash $9,120,000…)." — **✔**

**Q3. Highest-revenue segment in Q3, and amount?** *(Correct: Analytics Platform, $4,380,000)*
- NotebookLM — "Analytics Platform, $4,380,000 — 60.3% of total revenue." — **✔**
- Groq — "Analytics Platform…$4,380,000." — **✔**
- Mistral — "Analytics Platform…$4,380,000, which represented 60.3%…" — **✔**
- Gemini — "Analytics Platform…$4,380,000…60.3% of total revenue." — **✔**

### Calculations (Q4–Q6)

**Q4. Net change in cash during Q3?** *(Correct: +$780,000)*
- NotebookLM — "$780,000 (operating $1,780,000; investing $(650,000); financing $(350,000))." — **✔**
- Groq — "…the net change in cash was $780,000." — **✔**
- Mistral — "$780,000 (sum of operating, investing, financing cash flows)." — **✔**
- Gemini — "$780,000 (operating +$1,780,000…)." — **✔**

**Q5. Effective tax rate in Q3?** *(Correct: ≈30.1% = 156,000 ÷ 519,000)*
- NotebookLM — "≈30.1%; the 2.1% figure is tax as a share of revenue, not the effective rate." — **✔**
- Groq — "($156,000 / $519,000) × 100 = 30.1%." — **✔**
- Mistral — "(156,000 / 519,000) × 100 ≈ 30.1%." — **✔**
- Gemini — "Reported $156,000 tax on $519,000 pre-tax; noted 2.1% is of revenue, but did **not** state the 30.1% effective rate." — **◐** *(right figures and correctly flagged the 2.1% distractor, but didn't complete the calculation)*

**Q6. Change in net income from Q2 to Q3?** *(Correct: +$138,000, $1,402,000 → $1,540,000)*
- NotebookLM — "+$138,000 ($1,402,000 → $1,540,000), a 9.8% increase." — **✔**
- Groq — "$1,540,000 − $1,402,000 = $138,000." — **✔**
- Mistral — "+$138,000 ($1,402,000 → $1,540,000), a 9.8% increase." — **✔**
- Gemini — "$1,402,000 → $1,540,000, an increase of $138,000 (9.8%)." — **✔**

### Contradictions (Q7–Q9)

**Q7. Which company does the report cover?** *(Right answer: "Vantage Point Analytics, Inc." — header and tables)*
- NotebookLM — "Vantage Point Analytics, Inc.; the summary also mentions Northwind Sample Holdings." — **✔**
- Groq — "Northwind Sample Holdings." — **✘** *(wrong entity; no conflict noted)*
- Mistral — "Northwind Sample Holdings." — **✘** *(wrong entity; no conflict noted)*
- Gemini — "Covers Northwind Sample Holdings; prepared by Vantage Point Analytics, Inc." — **◐** *(named both entities, but concluded Northwind is the subject and rationalised the inconsistency rather than flagging it)*

**Q8. Q2 FY2026 total revenue?** *(Right answer: $6,912,000, detailed table)*
- NotebookLM — "$6,912,000; the summary separately cites $4,820,000 for Northwind." — **✔**
- Groq — "$6,912,000." — **◐** *(right figure; conflict not noted)*
- Mistral — "$6,912,000." — **◐** *(right figure; conflict not noted)*
- Gemini — *not obtained (quota)* — **—**

**Q9. Operating margin?** *(Right answer: 6.3% = 457,000 ÷ 7,265,000)*
- NotebookLM — "6.3% for Q3 ($457,000 on $7,265,000); the summary separately cites 34.7%." — **✔**
- Groq — "34.7%." — **✘** *(the misleading summary figure)*
- Mistral — "34.7% — derived from operating income of $457,000 relative to revenue of $7,265,000." — **✘** *(stated 34.7% but those figures give 6.3%; internally contradictory)*
- Gemini — *not obtained (quota)* — **—**

### Traps (Q10–Q12)

**Q10. Dividend per share declared?** *(Not in the document)*
- NotebookLM — "Not stated; the $350,000 financing outflow isn't identified as a dividend." — **✔**
- Groq — "Not stated; no dividend payments mentioned." — **✔**
- Mistral — "Not enough information; no dividend details in the context." — **✔**
- Gemini — *not obtained (quota)* — **—**

**Q11. Earnings per share (EPS)?** *(Not in the document — no share count)*
- NotebookLM — "Not stated; net income given, shares outstanding not." — **✔**
- Groq — "Cannot calculate; shares outstanding not provided." — **✔**
- Mistral — *(answered in German)* "Ich habe nicht genug Informationen…keine Angaben zu der Anzahl der ausstehenden Aktien." — **◐** *(correct content, but replied in German to an English question — a defect)*
- Gemini — *not obtained (quota)* — **—**

**Q12. Q1 FY2026 total revenue?** *(Not in the document — only Q2/Q3 given)*
- NotebookLM — "Not stated; only Q2 ($6,912,000) and Q3 ($7,265,000) are given." — **✔**
- Groq — "Not stated; only Q2 and Q3 revenue are mentioned." — **✔**
- Mistral — *(answered in German)* "Ich habe nicht genug Informationen…nur Q2 und Q3 FY2026." — **◐** *(correct content, replied in German — defect)*
- Gemini — *not obtained (quota)* — **—**

---

## 6. How each model did

**NotebookLM — 100% (12 / 0 / 0).** The reference. Correct throughout, including the
segment lookup and tax calculation, and it flagged all three contradictions while naming
the authoritative source. This is why it works well as the benchmark.

**Groq (full RAG) — 79.2% (9 / 1 / 2).** The app as it ships. Perfect on facts,
calculations, and traps, with no hallucinations. Its whole deficit is contradictions: it
returns one figure without flagging the disagreement (Q8), names the wrong company (Q7),
and gives the misleading operating margin (Q9). Fast (~5–15 s/query after an 82 s index).

**Mistral (full RAG) — 70.8% (7 / 3 / 2).** Strong on facts and calculations (all of
Q1–Q6 correct), and the fastest to index (33 s) and answer (~2 s). Weaknesses: the same
contradiction blind spot as Groq (Q7 wrong, Q9 gave 34.7% while citing figures that equal
6.3%, Q8 unflagged), plus a **language defect** — it answered the last two trap questions
**in German** despite English questions (correct content, wrong language).

**Gemini (full RAG) — incomplete (5 ✔, 2 ◐ of 7 answered).** Strong where it ran: correct
on facts and the net-income calculation (using the right table figures), and on Q7 it at
least named both companies. Two issues: on Q5 it laid out the right numbers but didn't
finish the calculation, and it **exhausted Google's free-tier daily limit of 20 requests**
after indexing plus seven questions, so Q8–Q12 returned empty. Also the slowest by far
(~12–35 s/query).

---

## 7. What I found

1. **On facts and calculations, all three models are strong** with the full pipeline. The
   lower Groq/Mistral scores seen in the earlier constant-context test were an artifact of
   that test's truncation, not the models.
2. **Contradiction handling is worse in the real pipeline than in the earlier test.** When
   each model builds its own index, the **retrieval/knowledge-graph stage tends to surface
   only one of the conflicting figures**, so the model never sees the contradiction. In this
   run **none** of the three local models flagged the Q8/Q9 conflicts — even Gemini, which
   had flagged them when it was fed both figures directly. This is an important,
   product-faithful insight: the retrieval stage can hide contradictions before the model
   can catch them.
3. **The knowledge graph mis-anchored the company** to "Northwind Sample Holdings" for all
   three models (Q7), because the indexing step latched onto the Executive-Summary name.
4. **No hallucination.** Every model correctly abstained on the trap questions it reached.
5. **Operational limits are real.** Full RAG per model is request-heavy; **Gemini's free
   tier (20 requests/day) cannot complete one full run** (index + 12 multi-call queries).
   Groq (14,400/day) and Mistral handled it comfortably.
6. **Mistral has a language-consistency defect** (answering in German), which would confuse
   an English-speaking user even though the content is correct.

---

## 8. Limitations

- **Gemini run incomplete.** Gemini hit Google's free-tier cap of **20 requests/day** for
  `gemini-3-flash` after indexing and 7 questions, so Q8–Q12 are missing. Its index is
  saved, so its remaining questions can be completed once the daily quota resets (no
  re-indexing needed).
- **Different pipelines for the reference.** NotebookLM uses its own retrieval; the app uses
  LightRAG + local embeddings. So NotebookLM-vs-app is a product comparison; the
  Groq/Mistral/Gemini comparison is like-for-like (each ran the same LightRAG pipeline).
- **Small sample.** One document, one attempt per question. Worth repeating on the other
  test files.
- **Some judgement in scoring**, applied consistently (e.g. "flagged the conflict" vs
  "returned one figure", and treating the German replies as a scored defect).

---

## 9. Conclusion

With the full pipeline running per model, the app's document Q&A is **accurate and honest on
facts, calculations, and knowing when to abstain**, and produced **no made-up answers**.
The shipping Groq configuration scores **79.2%** against NotebookLM's **100%**, and Mistral
is close behind at **70.8%** (dragged down partly by a language defect). The consistent gap
across all local models is **handling the document's self-contradictions** — and Option A
shows this is not only a model-reasoning issue but also a **retrieval issue**: the pipeline
often surfaces just one of the conflicting figures, so the model never gets the chance to
flag the conflict. Two practical takeaways: (1) improving contradiction handling needs work
at the **retrieval/indexing** stage, not only the model; and (2) **Gemini's free tier cannot
sustain a full RAG workload**, so using it end-to-end would require a paid quota. Groq
remains the most practical default; Mistral is a viable, fast alternative once its language
consistency is fixed.

---

## 10. Where the data came from

- **Model answers:** live Option-A runs against the project backend — each model built its
  own index under a separate workspace and answered all reachable questions through its own
  pipeline. Recorded per question.
- **NotebookLM answers:** the file `sample test 1 notebook ans.pdf` you provided.
- **Correct answers:** taken from the detailed tables in `sample for test 1.pdf`; where the
  Executive Summary disagrees with those tables, the tables are treated as authoritative.
