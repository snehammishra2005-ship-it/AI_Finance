# Evaluation with NotebookLM — Test 2 (full RAG per model)

**Date:** 8 August 2026
**Method:** Each model was run in "full pipeline" mode — it builds its own index of the document and answers the 12 questions from it. NotebookLM's answers are the ones you provided. Every answer is scored individually against the document's detailed tables (treated as authoritative where the executive summary conflicts).
**Document:** `sample for test 2.pdf` — "Northwind Sample Holdings, Inc., Q2 FY2026," which contradicts itself in a few places, including a net income that does not reconcile with its own income statement.
**Status:** NotebookLM, Groq, and Mistral complete. **Gemini pending — see §5.**

**Sources compared:** NotebookLM (reference) · Groq (full RAG — what the app ships) · Mistral (full RAG) · Gemini (full RAG — not yet run).

**Scoring:** ✔ Right (correct; for conflicts, flagged it and/or gave the authoritative figure) · ◐ Partial (close but flawed) · ✘ Wrong (incorrect, unanswered, or the misleading figure). Score = Right 100%, Partial 50%, Wrong 0%.

---

## 1. Master table

| # | Question | NotebookLM | Groq | Mistral | Gemini |
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
| | **Score** | **95.8%** | **79.2%** | **62.5%** | **pending** |

---

## 2. Question-by-question — every answer, scored

*(Gemini not yet run — see §5.)*

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
- NotebookLM — "Product Sales, $3,102,000 (64.4%)." — **✔**
- Groq — "Product Sales, $3,102,000 (64.4%)." — **✔**
- Mistral — "Product Sales, $3,102,000 (64.4%)." — **✔**

### Calculations (Q4–Q6)

**Q4. Net change in cash during Q2?** *(Correct: +$730,000)*
- NotebookLM — "$730,000." — **✔**
- Groq — "$730,000." — **✔**
- Mistral — "$730,000." — **✔**

**Q5. Effective tax rate in Q2?** *(Correct: ≈30.1% = 148,000 ÷ 492,500)*
- NotebookLM — "≈30.05% ($148,000 ÷ $492,500)." — **✔**
- Groq — "($148,000 / $492,500) × 100 ≈ 30.0%." — **✔**
- Mistral — "3.1% … based on $148,000 tax on $492,500 pre-tax income." — **✘** *(3.1% is tax as a % of revenue; those operands equal 30% — the same error as Test 1)*

**Q6. Change in net income from Q1 to Q2?** *(Correct: +$177,200, $1,015,300 → $1,192,500)*
- NotebookLM — "+$177,200 ($1,015,300 → $1,192,500)." — **✔**
- Groq — "$1,192,500 − $1,015,300 = $177,200." — **✔**
- Mistral — "+$177,200, a 17.5% increase." — **✔**

### Contradictions (Q7–Q9)

**Q7. Operating margin in Q2?** *(Authoritative: 9.4% = $452,000 ÷ $4,820,000; the Exec Summary's 34.7% is misleading)*
- NotebookLM — "Exec Summary says 34.7%; the detailed statement shows 9.4% operating-income margin; the 34.7% is based on the $3,145,000 operating-expense figure." — **✔** *(flagged the conflict, explained both)*
- Groq — "34.7%, based on operating expenses of $3,145,000." — **✘** *(the misleading figure; no conflict flagged)*
- Mistral — "34.7% — Operating Income $452,000 / Total Revenue $4,820,000 ≈ 34.7%." — **✘** *(states 34.7% but its own division equals 9.4%; internally contradictory)*

**Q8. Total operating expenses in Q2?** *(Authoritative: $2,445,000, detailed line items; the summary's $3,145,000 is the outlier)*
- NotebookLM — "The summary table lists $3,145,000. However, the detailed breakdown (S&M, R&D, G&A) totals $2,445,000." — **✔** *(flagged the conflict, gave both)*
- Groq — "$3,145,000." — **✘** *(the non-authoritative summary figure; no conflict flagged)*
- Mistral — "$3,145,000." — **✘** *(same)*

**Q9. Net income in Q2, and does it reconcile with the income statement?** *(Reported $1,192,500, but Income Before Tax $492,500 − Tax $148,000 = $344,500 — it does NOT reconcile; the "rounding adjustment" note can't explain an ~$848k gap)*
- NotebookLM — "$1,192,500. The report notes this figure reflects a 'small rounding adjustment for illustrative purposes'." — **◐** *(gave the figure and surfaced the caveat, but accepted the rounding explanation and didn't catch the ~$848k mismatch)*
- Groq — "$1,192,500. [Walks the P&L to Income Before Tax $492,500.] …we cannot reconcile it with the income statement using the information provided." — **◐** *(recognised it does not reconcile — the strongest answer here — but didn't name the implied $344,500)*
- Mistral — "$1,192,500 … after accounting for all revenues, expenses, and taxes … further supports the reconciliation." — **✘** *(wrongly asserts it reconciles)*

### Traps (Q10–Q12)

**Q10. Dividend per share declared?** *(Not in the document)*
- NotebookLM — "Not stated; the $190,000 financing outflow isn't identified as a dividend." — **✔**
- Groq — "Not stated; no dividend/per-share information." — **✔**
- Mistral — "Not enough information; no dividend details." — **✔**

**Q11. Earnings per share (EPS)?** *(Not in the document — no share count)*
- NotebookLM — "Not stated; net income given, shares outstanding not." — **✔**
- Groq — "Cannot calculate; shares outstanding not provided." — **✔**
- Mistral — "Not enough information; no EPS data." — **✔**

**Q12. Q3 FY2026 total revenue?** *(Not in the document — only Q1 and Q2 given)*
- NotebookLM — "Not available; the report only covers up to Q2 FY2026." — **✔**
- Groq — "Not enough information; only Q1 and Q2 are provided." — **✔**
- Mistral — *(answered in German)* "Ich habe nicht genug Informationen … nur Q1 FY2026 und Q2 FY2026." — **◐** *(correct content, wrong language)*

---

## 3. Results by model

**NotebookLM — 95.8% (11 / 1 / 0).** The reference, and the strongest — but not perfect. It
handled the operating-margin and operating-expenses conflicts (Q7, Q8) exactly right,
presenting both figures and explaining where each comes from. Its one slip was the
reconciliation question (Q9): it accepted the document's "small rounding adjustment" note
instead of noticing the net income can't foot (~$848k off).

**Groq — 79.2% (9 / 1 / 2).** The app as it ships. Perfect on facts, calculations, and traps,
with no hallucinations. On Q9 it arguably beat the reference — it worked the income statement
down to Income Before Tax $492,500 and concluded the reported net income "cannot be
reconciled." Its weaknesses are the other two contradictions (Q7 gave 34.7%; Q8 gave
$3,145,000), where it returned one figure without flagging the disagreement.

**Mistral — 62.5% (7 / 1 / 4).** Strong on facts and traps, and fast, but it accumulated
errors: it repeated the "3.1%" tax-rate mistake from Test 1 (Q5), stated 34.7% on Q7 while its
own arithmetic equals 9.4% (internally contradictory), gave the non-authoritative
operating-expenses figure (Q8), and wrongly claimed the net income reconciles (Q9). It also
answered Q12 in German — correct content, wrong language.

**Gemini — not yet run.** See §5.

---

## 4. Key findings

1. **The reconciliation trap (Q9) was the hardest — it caught even NotebookLM.** Only Groq
   flagged that the reported net income doesn't reconcile; NotebookLM accepted the rounding
   note, and Mistral claimed it reconciles. This is the one place the shipping app
   outperformed the reference.
2. **NotebookLM handled the other two contradictions cleanly** (Q7, Q8), presenting both the
   summary and detailed figures. The local models did not.
3. **The local models' contradiction blind spot persists** — Groq and Mistral both returned
   the Executive-Summary figures (34.7%, $3,145,000) without flagging the conflict, consistent
   with the retrieval stage surfacing one figure and burying the disagreement.
4. **Mistral has recurring defects:** the "% of revenue vs effective tax rate" confusion (Q5)
   and answering in German (Q12) both recurred from Test 1.
5. **No hallucinations** — every source correctly abstained on all three traps.

---

## 5. Gemini — current situation

**Gemini's Test 2 column is not filled, and it's blocked by a hard quota limit — not a bug.**

- A **full Option-A Gemini run** (build its own index + answer 12 questions) costs **~30 API
  requests** in mix mode (indexing fires several entity-extraction calls; each query fires a
  keyword-extraction call plus a synthesis call).
- Google's **free tier allows only 20 Gemini requests per day**. So a full Test 2 Gemini run
  **cannot complete in a single day** — this is the same wall that stopped the Test 1 run at
  Q8 the first time.
- Today's remaining quota was additionally spent finishing Test 1's Gemini answers and
  verifying the new persona-aware RAG feature, so **no full Test 2 run is possible today**.

**Options to complete Gemini's Test 2 column:**
1. **Paid Gemini quota** — enables a true Option-A run, fully comparable to Groq/Mistral above.
2. **Option B (free, ~12 requests)** — Gemini answers over a Groq-built Test 2 index (retrieval
   done once by Groq; Gemini only synthesises the 12 answers). Feasible on a fresh day, but a
   *different method* than the Groq/Mistral runs here, so its column would be labelled as such.
3. **Leave Test 2 as a three-way** (NotebookLM vs Groq vs Mistral).

For reference, in **Test 1** Gemini (full RAG) scored **91.7%** — the strongest of the app's
models — so it would be expected to perform well here too once it can be run.

---

## 6. Caveats

- NotebookLM uses its own retrieval; the app uses LightRAG + local embeddings + the chosen model. So NotebookLM-vs-app is a product comparison; Groq-vs-Mistral is like-for-like.
- One document, one attempt per question — worth repeating on further test files.
- Some judgement in the conflict/defect scoring (e.g. Q9 "recognised non-reconciliation" vs "accepted the rounding note"; German answers as a defect), applied the same way to every model.
- Correct answers come from the detailed tables in `sample for test 2.pdf`; where the executive summary conflicts, the tables are treated as authoritative.
