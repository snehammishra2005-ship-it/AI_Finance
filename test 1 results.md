# Evaluation with NotebookLM — Test 1 (full RAG per model)

**Date:** 8 August 2026
**Method:** Each model was run in "full pipeline" mode — it builds its own index of the document and answers the 12 questions from it. NotebookLM's answers are the ones you provided. Every answer is scored individually against the document's detailed tables (treated as authoritative where the executive summary conflicts).
**Document:** `sample for test 1.pdf` — "Vantage Point Analytics, Inc., Q3 FY2026," which deliberately contradicts itself in a few places.

**Sources compared:** NotebookLM (reference) · Groq (full RAG — what the app ships) · Mistral (full RAG) · Gemini (full RAG).

**Scoring:** ✔ Right (correct; for conflicts, flagged it and/or gave the authoritative figure) · ◐ Partial (close but flawed — right figure but no conflict flagged, right setup but math unfinished, or right content in the wrong language) · ✘ Wrong (incorrect, unanswered, or the misleading figure). Score = Right 100%, Partial 50%, Wrong 0%.

---

## 1. Master table

| # | Question | NotebookLM | Groq | Mistral | Gemini |
|---|----------|:---:|:---:|:---:|:---:|
| 1 | Q3 revenue | ✔ | ✔ | ✔ | ✔ |
| 2 | Total assets | ✔ | ✔ | ✔ | ✔ |
| 3 | Top segment | ✔ | ✔ | ✔ | ✔ |
| 4 | Net change in cash | ✔ | ✔ | ✔ | ✔ |
| 5 | Effective tax rate | ✔ | ✔ | ✔ | ◐ |
| 6 | Net income change | ✔ | ✔ | ✔ | ✔ |
| 7 | Company (conflict) | ✔ | ✘ | ✘ | ◐ |
| 8 | Q2 revenue (conflict) | ✔ | ◐ | ◐ | ✔ |
| 9 | Operating margin (conflict) | ✔ | ✘ | ✘ | ✔ |
| 10 | Dividend (trap) | ✔ | ✔ | ✔ | ✔ |
| 11 | EPS (trap) | ✔ | ✔ | ◐ | ✔ |
| 12 | Q1 revenue (trap) | ✔ | ✔ | ◐ | ✔ |
| | **Right (✔)** | **12** | 9 | 7 | 10 |
| | **Partial (◐)** | 0 | 1 | 3 | 2 |
| | **Wrong (✘)** | 0 | 2 | 2 | 0 |
| | **Score** | **100%** | **79.2%** | **70.8%** | **91.7%** |

---

## 2. Question-by-question — every answer, scored

### Facts (Q1–Q3)

**Q1. Total revenue in Q3 FY2026?** *(Correct: $7,265,000)*
- NotebookLM — "$7,265,000; a 5.1% increase over Q2's $6,912,000." — **✔**
- Groq — "$7,265,000." — **✔**
- Mistral — "$7,265,000." — **✔**
- Gemini — "$7,265,000; a 5.1% increase over the $6,912,000 in Q2." — **✔**

**Q2. Total assets as of 30 Sep 2026?** *(Correct: $20,380,000)*
- NotebookLM — "$20,380,000 (current $14,450,000; PP&E $4,610,000; intangibles $1,320,000)." — **✔**
- Groq — "$20,380,000." — **✔**
- Mistral — "$20,380,000." — **✔**
- Gemini — "$20,380,000." — **✔**

**Q3. Highest-revenue segment in Q3, and how much?** *(Correct: Analytics Platform, $4,380,000)*
- NotebookLM — "Analytics Platform, $4,380,000 — 60.3% of total revenue." — **✔**
- Groq — "Analytics Platform, $4,380,000." — **✔**
- Mistral — "Analytics Platform, $4,380,000 (60.3%)." — **✔**
- Gemini — "Analytics Platform, $4,380,000 (60.3%)." — **✔**

### Calculations (Q4–Q6)

**Q4. Net change in cash during Q3?** *(Correct: +$780,000)*
- NotebookLM — "$780,000 (operating $1,780,000; investing $(650,000); financing $(350,000))." — **✔**
- Groq — "$780,000." — **✔**
- Mistral — "$780,000." — **✔**
- Gemini — "$780,000." — **✔**

**Q5. Effective tax rate in Q3?** *(Correct: ≈30.1% = 156,000 ÷ 519,000)*
- NotebookLM — "≈30.1% (pre-tax $519,000; tax $156,000). The 2.1% figure is tax as a share of revenue." — **✔**
- Groq — "($156,000 / $519,000) × 100 = 30.1%." — **✔**
- Mistral — "(156,000 / 519,000) × 100 ≈ 30.1%." — **✔**
- Gemini — "Laid out pre-tax $519,000 and tax $156,000, but didn't state the 30.1% rate." — **◐** *(right figures, didn't finish the calculation)*

**Q6. Change in net income from Q2 to Q3?** *(Correct: +$138,000, $1,402,000 → $1,540,000)*
- NotebookLM — "+$138,000 ($1,402,000 → $1,540,000), a 9.8% increase." — **✔**
- Groq — "$1,540,000 − $1,402,000 = $138,000." — **✔**
- Mistral — "+$138,000 ($1,402,000 → $1,540,000)." — **✔**
- Gemini — "$1,402,000 → $1,540,000, an increase of $138,000." — **✔**

### Contradictions (Q7–Q9)

**Q7. Which company does the report cover?** *(Right answer: "Vantage Point Analytics, Inc." — header and tables)*
- NotebookLM — "Vantage Point Analytics, Inc.; the summary also mentions Northwind Sample Holdings." — **✔**
- Groq — "Northwind Sample Holdings." — **✘** *(wrong name; conflict not flagged)*
- Mistral — "Northwind Sample Holdings." — **✘**
- Gemini — "Covers Northwind Sample Holdings; prepared by Vantage Point Analytics, Inc." — **◐** *(named both, but concluded Northwind rather than flagging the conflict)*

**Q8. Q2 FY2026 total revenue?** *(Right answer: $6,912,000 — the detailed table)*
- NotebookLM — "$6,912,000; the summary separately cites $4,820,000 for Northwind." — **✔**
- Groq — "$6,912,000." — **◐** *(right figure, conflict not flagged)*
- Mistral — "$6,912,000." — **◐** *(right figure, conflict not flagged)*
- Gemini — "Two figures: summary $4,820,000 vs tables $6,912,000; the $6,912,000 is the Q3 baseline." — **✔** *(flagged the conflict and picked the right figure)*

**Q9. Operating margin?** *(Right answer: 6.3% = $457,000 ÷ $7,265,000; the 34.7% belongs to a different (Q2) figure in the summary)*
- NotebookLM — "6.3% for Q3 ($457,000 on $7,265,000); the summary cites 34.7% for Q2." — **✔**
- Groq — "34.7%." — **✘** *(the misleading summary figure)*
- Mistral — "34.7%." — **✘**
- Gemini — "Q2 34.7%; Q3 6.3% ($457,000 on $7,265,000)." — **✔** *(gave both, with the right Q3 figure)*

### Traps (Q10–Q12)

**Q10. Dividend per share declared?** *(Not in the document)*
- NotebookLM — "Not stated; the $350,000 financing outflow isn't identified as a dividend." — **✔**
- Groq — "Not stated." — **✔**
- Mistral — "Not enough information." — **✔**
- Gemini — "No information regarding dividends." — **✔**

**Q11. Earnings per share (EPS)?** *(Not in the document — no share count)*
- NotebookLM — "Not stated; net income given, shares outstanding not." — **✔**
- Groq — "Cannot calculate; shares outstanding not provided." — **✔**
- Mistral — *(answered in German)* "Ich habe nicht genug Informationen…" — **◐** *(correct content, wrong language)*
- Gemini — "No information on EPS; net income $1,540,000 given but no share count." — **✔**

**Q12. Q1 FY2026 total revenue?** *(Not in the document — only Q2/Q3 given)*
- NotebookLM — "Not stated; only Q2 and Q3 given." — **✔**
- Groq — "Not stated; only Q2 and Q3 mentioned." — **✔**
- Mistral — *(answered in German)* "Ich habe nicht genug Informationen…" — **◐** *(correct content, wrong language)*
- Gemini — "Q1 not stated; Q2 $6,912,000 and Q3 $7,265,000 given." — **✔**

---

## 3. Results by model

**NotebookLM — 100% (12 / 0 / 0).** Correct throughout, including the segment look-up and the
tax calculation, and it flagged all three contradictions while naming the authoritative figure.

**Gemini — 91.7% (10 / 2 / 0).** The best of the app's models and the only one to catch the
contradictions (Q8, Q9), giving both figures and identifying the right one; never wrong. Two
slips: Q5 (right figures, didn't finish the calculation) and Q7 (named both companies but
concluded "Northwind"). Slowest, and its free tier (20 requests/day) can't finish a full run in
one day.

**Groq — 79.2% (9 / 1 / 2).** The app as it ships. Perfect on facts, calculations, and traps,
with no hallucinations. Its whole deficit is contradictions: one figure without flagging the
disagreement (Q8), the wrong company (Q7), and the misleading operating margin (Q9). Fastest.

**Mistral — 70.8% (7 / 3 / 2).** Good on facts and calculations, and fast, but it shares Groq's
contradiction blind spot (Q7, Q9 wrong; Q8 unflagged) and answered the last two traps **in
German** — right content, wrong language.

---

## 4. Key findings

1. **No hallucination** from any source on the trap questions.
2. **Facts and calculations match the reference** — the shipping Groq pipeline equals NotebookLM there.
3. **Contradictions separate the models:** NotebookLM flagged all three, Gemini two of three, Groq and Mistral none.
4. **Model choice is the biggest lever:** on the same pipeline, Gemini (91.7%) beat Groq (79.2%) and Mistral (70.8%). The app is Groq-only for document Q&A today.
5. **Gemini's free tier can't sustain a full run** (~26–28 requests > 20/day), so end-to-end use needs a paid quota.
6. **Mistral has a language defect** (answering in German).

---

## 5. Caveats

- NotebookLM uses its own retrieval; the app uses LightRAG + local embeddings + the chosen model. So NotebookLM-vs-app is a product comparison; the three app models against each other is like-for-like.
- Gemini's run was split across two days because of its daily quota (doesn't change the answers).
- One document, one attempt per question — worth repeating on the other test files.
- Some judgement in the conflict/defect scoring, applied the same way to every model.
- Correct answers come from the detailed tables in `sample for test 1.pdf`; where the executive summary conflicts, the tables are treated as authoritative.
