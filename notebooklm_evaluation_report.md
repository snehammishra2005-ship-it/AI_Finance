# Evaluating the AI-in-Finance Document Q&A against NotebookLM (Test 1)

**Date:** 2 August 2026
**Prepared by:** AI-in-Finance project team
**Scope:** Comparing the app's document question-answering to NotebookLM, and comparing the project's three working models (Groq, Mistral, Gemini) on the same questions.
**Test file:** `sample for test 1.pdf` — a quarterly finance report for "Vantage Point Analytics, Inc. (Q3 FY2026)" that intentionally contradicts itself in a few places.

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

The goal was to check how good the app's document Q&A really is, using **NotebookLM as a
reference** ("what a strong tool answers"), and to see whether the other models the project
already integrates would do any better than the current one. The test document was chosen
because it contradicts itself in a few spots, which is a good way to see whether a system
notices problems or just answers confidently.

---

## 2. What I tested and how

I asked the **same 12 questions** to five answer sources:

| Source | What it is |
|--------|-----------|
| **NotebookLM** | The reference we compare against (its own answers on the full document). |
| **App RAG (Groq)** | The app exactly as it runs today (`/rag/ask`, full context, Groq model). |
| **Groq (test)** | A model-comparison run — same retrieved context for every model, Groq answering. |
| **Mistral (test)** | Same setup, Mistral answering. |
| **Gemini (test)** | Same setup, Gemini answering. |

The 12 questions cover four skills:

- **Facts** (Q1–Q3) — look up a number.
- **Calculations** (Q4–Q6) — work something out.
- **Contradictions** (Q7–Q9) — the document disagrees with itself here.
- **Traps** (Q10–Q12) — the answer isn't in the document, so the right move is to say so.

The "App RAG (Groq)" run reflects the app as shipped. The three "(test)" runs keep the
retrieved context identical so the only thing changing is the model — a fairer way to
compare models.

---

## 3. How answers were scored

| Rating | Symbol | Meaning |
|--------|:---:|---------|
| Right | ✔ | Correct. For contradiction questions, it pointed out the conflict and gave the right figure. |
| Partial | ◐ | Close but flawed — e.g., gave the right figure but didn't mention the conflict, or spotted the conflict but did the math wrong. |
| Wrong | ✘ | Incorrect, didn't answer, or gave the misleading figure. |

Score = Right 100%, Partial 50%, Wrong 0%, averaged over the 12 questions.

---

## 4. Results at a glance

**Legend:** ✔ = Right · ◐ = Partial · ✘ = Wrong

| # | Question | NotebookLM | App RAG (Groq) | Groq (test) | Mistral (test) | Gemini (test) |
|---|----------|:---:|:---:|:---:|:---:|:---:|
| 1 | Q3 revenue | ✔ | ✔ | ✔ | ✔ | ✔ |
| 2 | Total assets | ✔ | ✔ | ✔ | ✔ | ✔ |
| 3 | Top segment | ✔ | ✔ | ✘ | ✘ | ✘ |
| 4 | Net change in cash | ✔ | ✔ | ✔ | ✔ | ✔ |
| 5 | Effective tax rate | ✔ | ✔ | ✘ | ✘ | ✔ |
| 6 | Net income change | ✔ | ✔ | ✘ | ✘ | ◐ |
| 7 | Company (conflict) | ✔ | ✘ | ✘ | ◐ | ✔ |
| 8 | Q2 revenue (conflict) | ✔ | ◐ | ◐ | ✘ | ✔ |
| 9 | Operating margin (conflict) | ✔ | ✘ | ✘ | ✘ | ✔ |
| 10 | Dividend (trap) | ✔ | ✔ | ✔ | ✔ | ✔ |
| 11 | EPS (trap) | ✔ | ✔ | ✔ | ✔ | ✔ |
| 12 | Q1 revenue (trap) | ✔ | ✔ | ✔ | ✔ | ✔ |
| | **Right (✔)** | **12** | 9 | 6 | 6 | 10 |
| | **Partial (◐)** | 0 | 1 | 1 | 1 | 1 |
| | **Wrong (✘)** | 0 | 2 | 5 | 5 | 1 |
| | **Score** | **100%** | **79.2%** | **54.2%** | **54.2%** | **87.5%** |

---

## 5. Question-by-question answers and scores

Each answer is quoted from the actual output and rated on its own.

### Facts (Q1–Q3)

**Q1. Total revenue in Q3 FY2026?** *(Correct answer: $7,265,000)*
- NotebookLM — "$7,265,000; a 5.1% increase over the $6,912,000 in Q2." — **✔**
- App RAG (Groq) — "$7,265,000." — **✔**
- Groq (test) — "$7,265,000" — **✔**
- Mistral (test) — "$7,265,000" — **✔**
- Gemini (test) — "$7,265,000." — **✔**

**Q2. Total assets as of 30 Sep 2026?** *(Correct answer: $20,380,000)*
- NotebookLM — "$20,380,000 (current $14,450,000; PP&E $4,610,000; intangibles $1,320,000)." — **✔**
- App RAG (Groq) — "$20,380,000." — **✔**
- Groq (test) — "$20,380,000" — **✔**
- Mistral (test) — "$20,380,000" — **✔**
- Gemini (test) — "$20,380,000." — **✔**

**Q3. Highest-revenue segment in Q3, and how much?** *(Correct answer: Analytics Platform, $4,380,000)*
- NotebookLM — "Analytics Platform, $4,380,000 — 60.3% of total revenue." — **✔**
- App RAG (Groq) — "Analytics Platform, $4,380,000 (Revenue by Segment table, page 2)." — **✔**
- Groq (test) — "Not stated in the document." — **✘** *(the context cap cut the segment table)*
- Mistral (test) — "Not stated in the document." — **✘** *(context cap)*
- Gemini (test) — "Not stated; segment names are present but the figures are missing." — **✘** *(context cap)*

### Calculations (Q4–Q6)

**Q4. Net change in cash during Q3?** *(Correct answer: +$780,000)*
- NotebookLM — "$780,000 (operating $1,780,000; investing $(650,000); financing $(350,000); cash $8,340,000 → $9,120,000)." — **✔**
- App RAG (Groq) — "$1,780,000 − $650,000 − $350,000 = $780,000." — **✔**
- Groq (test) — "$780,000." — **✔**
- Mistral (test) — "$780,000." — **✔**
- Gemini (test) — "$780,000." — **✔**

**Q5. Effective tax rate in Q3?** *(Correct answer: ≈30.1% = 156,000 ÷ 519,000)*
- NotebookLM — "≈30.1% (pre-tax $519,000; tax $156,000). The 2.1% figure is tax as a share of revenue, not the effective rate." — **✔**
- App RAG (Groq) — "$156,000 ÷ $519,000 ≈ 30.1%." — **✔**
- Groq (test) — "Not stated in the document." — **✘** *(context cap cut the tax figures)*
- Mistral (test) — "2.1%." — **✘** *(that's tax as a % of revenue, not the effective rate)*
- Gemini (test) — "≈30.06% ($156,000 ÷ $519,000); notes 2.1% is of revenue." — **✔**

**Q6. Change in net income from Q2 to Q3?** *(Correct answer: +$138,000, $1,402,000 → $1,540,000)*
- NotebookLM — "+$138,000 ($1,402,000 → $1,540,000), a 9.8% increase." — **✔**
- App RAG (Groq) — "$1,540,000 − $1,402,000 = $138,000." — **✔**
- Groq (test) — "Not stated in the document." — **✘**
- Mistral (test) — "Not stated in the document." — **✘**
- Gemini (test) — "Conflict noted: page-1 Q2 $1,192,500 vs page-2 Q3 $1,540,000 → +$347,500." — **◐** *(spotted a conflict, but used the wrong Q2 figure, so the result is off)*

### Contradictions (Q7–Q9)

**Q7. Which company does the report cover?** *(Right answer: "Vantage Point Analytics, Inc." — header and tables)*
- NotebookLM — "Vantage Point Analytics, Inc.; the summary also mentions Northwind Sample Holdings." — **✔**
- App RAG (Groq) — "Northwind Sample Holdings." — **✘** *(wrong name; didn't flag the conflict)*
- Groq (test) — "Northwind Sample Holdings." — **✘**
- Mistral (test) — "Vantage Point Analytics, Inc." — **◐** *(right name, but didn't flag the conflict)*
- Gemini (test) — "Vantage Point Analytics, Inc.; also mentions Northwind Sample Holdings." — **✔**

**Q8. Q2 FY2026 total revenue?** *(Right answer: $6,912,000 — the detailed table)*
- NotebookLM — "$6,912,000 (with segment detail); the summary separately cites $4,820,000 for Northwind." — **✔**
- App RAG (Groq) — "$6,912,000." — **◐** *(right figure, no mention of the conflict)*
- Groq (test) — "$6,912,000." — **◐** *(right figure, no mention of the conflict)*
- Mistral (test) — "$4,820,000." — **✘** *(the weaker summary figure)*
- Gemini (test) — "Conflicting figures: $4,820,000 (summary) vs $6,912,000 (table)." — **✔**

**Q9. Operating margin?** *(Right answer: 6.3% = 457,000 ÷ 7,265,000)*
- NotebookLM — "6.3% for Q3 ($457,000 on $7,265,000); the summary separately cites 34.7% for Q2." — **✔**
- App RAG (Groq) — "34.7% in Q2 FY2026." — **✘** *(the misleading summary figure)*
- Groq (test) — "34.7%." — **✘** *(misleading figure)*
- Mistral (test) — "Not stated in the document." — **✘** *(didn't answer)*
- Gemini (test) — "Conflicting figures: 34.7% (summary) vs 6.3% (from the income statement)." — **✔**

### Traps (Q10–Q12)

**Q10. Dividend per share declared?** *(Not in the document)*
- NotebookLM — "Not stated; the $350,000 financing outflow isn't identified as a dividend." — **✔**
- App RAG (Groq) — "Not stated; no dividend or per-share amounts mentioned." — **✔**
- Groq (test) — "Not stated in the document." — **✔**
- Mistral (test) — "Not stated in the document." — **✔**
- Gemini (test) — "Not stated in the document." — **✔**

**Q11. Earnings per share (EPS)?** *(Not in the document — no share count)*
- NotebookLM — "Not stated; net income ($1,540,000) is given but shares outstanding aren't." — **✔**
- App RAG (Groq) — "Can't be calculated; shares outstanding not provided." — **✔**
- Groq (test) — "Not stated in the document." — **✔**
- Mistral (test) — "Not stated in the document." — **✔**
- Gemini (test) — "Not stated in the document." — **✔**

**Q12. Q1 FY2026 total revenue?** *(Not in the document — only Q2/Q3 given)*
- NotebookLM — "Not stated; tables compare only Q2 ($6,912,000) and Q3 ($7,265,000)." — **✔**
- App RAG (Groq) — "Not stated; only Q2 and Q3 revenue are given." — **✔**
- Groq (test) — "Not stated in the document." — **✔**
- Mistral (test) — "Not stated in the document." — **✔**
- Gemini (test) — "Not stated; context includes only Q2 and Q3." — **✔**

---

## 6. How each model did

**NotebookLM — 100% (12 / 0 / 0).** Got everything right, including the segment lookup
(Q3) and the tax calculation (Q5, where it also explained why 2.1% is a trap). It pointed
out all three contradictions and named the correct source each time. This is why it works
well as the reference.

**Gemini — 87.5% (10 / 1 / 1).** The best of the project's own models here. It calculated
the tax rate and flagged the contradictions much like NotebookLM. It lost Q3 to the context
cap, and on Q6 it noticed a conflict but did the subtraction with the wrong number. Slowest
to respond (~10–12s).

**App RAG (Groq) — 79.2% (9 / 1 / 2).** This is the app as it runs today. It matched
NotebookLM on every fact, calculation, and trap, and never made anything up. Its only weak
spot is contradictions: it gives one figure without flagging the disagreement (Q8), picks
the wrong company (Q7), and gives the misleading operating margin (Q9). This is the model's
behaviour, not missing data — it had the full context and still didn't flag the conflicts.
Fastest (~1–2s).

**Groq (test) — 54.2% (6 / 1 / 5).** Same model as the app, but on the capped test context,
so it lost Q3 and Q5 to truncation on top of the contradiction weakness. The 79.2% from the
app run is the fair number for Groq.

**Mistral — 54.2% (6 / 1 / 5).** Similar to Groq on facts and traps, and just as fast. Its
worst moment was Q5, where it gave a confident but wrong 2.1% — a confident wrong answer is
riskier than saying "not stated."

---

## 7. What I found

1. **Nothing was made up.** On all three trap questions, every source (the app included)
   correctly said the answer wasn't in the document.
2. **The app is as good as the reference on facts and math.** For straightforward lookups
   and calculations, App RAG (Groq) matched NotebookLM.
3. **The one real weakness is contradictions.** NotebookLM and Gemini point out when the
   document disagrees with itself and pick the reliable figure; the app just returns one
   number quietly, and once (Q9) the wrong one.
4. **The model you choose matters.** With the same context, Gemini came close to NotebookLM
   while Groq and Mistral fell behind. Right now the app's document Q&A can only use Groq.
5. **Spotting a conflict isn't the same as resolving it.** Q6 shows Gemini can flag a
   contradiction and still calculate from the wrong figure.

---

## 8. Limitations

- **Context cap on the test runs.** The model-comparison runs capped the shared context at
  8,000 characters, which cut the data for Q3 (all models) and Q5 (Groq). That lowers the
  Groq/Mistral test scores; the app run (79.2%) is the fair measure for Groq. NotebookLM and
  the app run aren't affected.
- **Different pipelines.** NotebookLM uses its own retrieval; the app uses LightRAG + Groq.
  So app-vs-NotebookLM is a product comparison, while Groq/Mistral/Gemini is a clean
  model comparison (same input).
- **Small sample.** One document, one attempt per question. Worth repeating on the other
  test files before drawing firm conclusions.
- **Some judgement in scoring.** "Flagged the conflict" vs "gave one figure quietly" is a
  call I made consistently across all sources.

---

## 9. Conclusion

On this test, the app's document Q&A is **accurate and honest** — it scored **79.2%**
against NotebookLM's **100%**, with **no made-up answers**, and it matched the reference on
facts, calculations, and knowing when to say "not in the document." The gap is in one
specific area: **noticing and correctly handling parts of a document that contradict each
other**, where the current Groq-based pipeline falls short. The model comparison suggests
this is largely a model issue — **Gemini scored 87.5%** on the same task. The most useful
next step would be to **let the document Q&A use a stronger model like Gemini** (at least as
an option for important documents), while keeping Groq for fast everyday questions.

---

## 10. Where the data came from

- **App answers:** live runs against the project backend — the real `/rag/ask` endpoint
  (Groq) and a multi-model test run (Groq/Mistral/Gemini) with the context held constant.
- **NotebookLM answers:** the file `sample test 1 notebook ans.pdf` you provided.
- **Correct answers:** taken from the detailed tables in `sample for test 1.pdf`; where the
  Executive Summary disagrees with those tables, I treated the tables as correct.
