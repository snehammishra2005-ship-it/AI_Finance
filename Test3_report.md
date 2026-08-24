# Evaluation with NotebookLM — Test 3 (full RAG per model, Student persona)

**Date:** 19–23 August 2026
**Method:** Each model answers the same 12 questions, grounded in its own RAG index, and worded for the **Student persona** (the app's persona-aware RAG feature, with the hard "never alter the numbers" guardrail active). NotebookLM's answers are the ones you provided. Gemini and Mistral ran **Option A** (full pipeline — each builds its own index and answers from it). **Groq is shown as two attempts** (see note). Every answer is scored individually against the document's figures.
**Document:** `finance report sample.pdf` — RBI *Financial Stability Report, June 2025* (Executive Summary). A large document; its size is the main stressor of this test (unlike Test 2's self-contradictions).

**Sources compared:** NotebookLM (reference) · Gemini (Option A, full RAG — complete) · Mistral (Option A, full RAG) · Groq (TRY 2 — trimmed context).

> **Groq ran twice.** **TRY 1** (full-context RAG, the app's normal path) **failed** — the retrieved context was ~14k tokens, over Groq's 6,000-tokens/minute free-tier limit, so every query returned `413 Request too large`. **TRY 2** re-ran with `gpt-oss-20b` and the context trimmed to `max_total_tokens=3000` to fit. The trim consumed the whole budget on the knowledge graph and left **0 document chunks** — so Groq answered from the graph alone, not the report's prose. Its column reflects a **degraded pipeline**, not the model's ceiling.

> **Persona guardrail.** This is the first test to use persona-aware RAG. Every answer was rewritten for a student (analogies, plain language) **while the figures were held exactly** — that guardrail also forbids inventing a number that isn't in the context, which is why the models abstain on the traps.

**Scoring:** ✔ Right (correct figure, or correctly abstained on a trap) · ◐ Partial (right direction, missing/imprecise figure) · ✘ Wrong (incorrect, hallucinated, or unanswered when the answer was in the document). Score = Right 100%, Partial 50%, Wrong 0%.

---

## 1. Master table

| # | Question | NotebookLM | Gemini (Opt A) | Mistral (Opt A) | Groq (TRY 2) |
|---|----------|:---:|:---:|:---:|:---:|
| 1 | GDP growth 2025-26 | ✔ | ✔ | ✔ | ✔ |
| 2 | Forex reserves / import cover | ✔ | ✔ | ✔ | ✘ |
| 3 | SCB Gross NPA ratio | ✔ | ✔ | ✔ | ✘ |
| 4 | Unsecured-credit CAGR slowdown | ✔ | ✔ | ✔ | ✘ |
| 5 | Household debt-to-GDP vs EM avg | ✔ | ✔ | ✔ | ✘ |
| 6 | Microfinance stressed-assets change | ✔ | ✔ | ✔ | ✘ |
| 7 | NBFC CRAR | ✔ | ✔ | ✔ | ◐ |
| 8 | Unsecured vs overall retail GNPA | ✔ | ✔ | ✔ | ◐ |
| 9 | Stress-test CRAR vs minimum | ✔ | ✔ | ✔ | ✘ |
| 10 | Repo rate (trap) | ✔ | ✔ | ✔ | ✔ |
| 11 | GDP growth 2026-27 (trap) | ✔ | ✔ | ✘ | ✔ |
| 12 | MPC last-meeting date (trap) | ✔ | ✔ | ✔ | ✔ |
| | **Right (✔)** | 12 | 12 | 11 | 4 |
| | **Partial (◐)** | 0 | 0 | 0 | 2 |
| | **Wrong (✘)** | 0 | 0 | 1 | 6 |
| | **Score** | **100%** | **100%** | **91.7%** | **41.7%** |

> Gemini's Option-A run spanned two days because a full run exceeds the free-tier 20-requests/day cap — Q1–Q10 on 19 Aug, the two remaining traps (Q11–Q12) after the 23 Aug quota reset. It answered all 12.

---

## 2. Question-by-question — every answer, scored

### Headline facts (Q1–Q3)

**Q1. India's projected real GDP growth for 2025-26?** *(Correct: 6.5%)*
- NotebookLM — "6.5% … fastest-growing major economy, supported by buoyant domestic demand." — **✔**
- Gemini — "**6.5%** … like a giant student club producing more 'stuff'; powered by domestic demand." — **✔**
- Mistral — "**6.5%** … like your school's annual day: 100 performers become 106.5." — **✔**
- Groq — "**6.5%**." *(the one figure that lived in the knowledge graph)* — **✔**

**Q2. Foreign-exchange reserves, and months of imports covered?** *(Correct: US$697.9 bn, >11 months)*
- NotebookLM — "US$697.9 billion; more than 11 months of imports." — **✔**
- Gemini — "**US$697.9 billion** … enough for more than **11 months of imports**; a cushion." — **✔**
- Mistral — "**US$697.9 billion** … covers **more than 11 months of imports**." — **✔**
- Groq — "I don't have enough information in the provided context." — **✘** *(the figure was in the prose, which the trim removed)*

**Q3. Scheduled commercial banks' Gross NPA (GNPA) ratio?** *(Correct: 2.3%, a multi-decadal low)*
- NotebookLM — "2.3% … multi-decadal low; better underwriting and resolution of legacy stress." — **✔**
- Gemini — "**2.3%** … 'homework completion rate'; a multi-decadal low." — **✔**
- Mistral — "**2.3%** … only 2–3 of every 100 rupees at risk." — **✔**
- Groq — "I don't have enough information to answer that." — **✘** *(not in the trimmed context)*

### Comparisons & calculations (Q4–Q6)

**Q4. By how much did the CAGR of unsecured retail credit slow?** *(Correct: 15.4 pp — 27.0% → 11.6%)*
- NotebookLM — "Slowed 15.4 pp: 27.0% (Sep 2021–Sep 2023) → 11.6% (Sep 2023–Mar 2025)." — **✔**
- Gemini — "**27.0% → 11.6%**, a drop of **15.4 percentage points** … like a car slowing from 27 to 11.6 km/h." — **✔**
- Mistral — "**27.0% − 11.6% = 15.4%** slowdown." — **✔**
- Groq — "I don't have enough information to calculate that difference." — **✘**

**Q5. Household debt-to-GDP vs the emerging-market average?** *(Correct: 41.9% vs 46.6%)*
- NotebookLM — "41.9% vs 46.6% EM average; Indian households less leveraged." — **✔**
- Gemini — "**41.9%** vs **46.6%** … like owing ₹419 vs ₹466 per ₹1,000 earned." — **✔**
- Mistral — "**41.9%** vs **46.6%** … ₹42 out of ₹100 vs ₹47 out of ₹100." — **✔**
- Groq — *(empty answer)* — **✘** *(the comparison figures existed only in prose)*

**Q6. Change in microfinance stressed assets, Sep 2024 → Mar 2025?** *(Correct: +2.0 pp, 3.9% → 5.9%)*
- NotebookLM — "Rose 2.0 pp, 3.9% → 5.9%; a 'notable deterioration'." — **✔**
- Gemini — "Increased from **3.9% to 5.9%** … a watchpoint." — **✔**
- Mistral — "**3.9% → 5.9%**, a jump of **2 percentage points** in six months." — **✔**
- Groq — *(empty answer)* — **✘**

### Sector detail (Q7–Q9)

**Q7. CRAR for the NBFC sector (not the banks)?** *(Correct: 25.8%)*
- NotebookLM — "25.8% … well above requirement; banks' CRAR is 17.3%." — **✔**
- Gemini — "**25.8%** … like a safety helmet; well above the minimum." — **✔**
- Mistral — "**25.8%** … ₹25.80 aside per ₹100 lent." — **✔**
- Groq — "**25%** … above the minimum." — **◐** *(right ballpark and direction, but the exact figure is 25.8%)*

**Q8. GNPA for unsecured retail vs the overall retail portfolio?** *(Correct: 1.8% vs 1.2%)*
- NotebookLM — "Unsecured 1.8% vs overall 1.2%; a watchpoint." — **✔**
- Gemini — "**Unsecured 1.8%**, **overall 1.2%** … like an attendance record." — **✔**
- Mistral — "**Unsecured 1.8%**, **overall 1.2%**." — **✔**
- Groq — "Unsecured is higher than the overall retail portfolio." — **◐** *(correct direction, both figures missing)*

**Q9. Under severe stress, does banks' CRAR stay above the minimum — and what is it?** *(Correct: yes; minimum 9%)*
- NotebookLM — "Yes; minimum is 9%; the 17.3% system CRAR acts as a shock absorber." — **✔**
- Gemini — "**Yes** … stays above the **9%** regulatory minimum; extra capital is a shock absorber." — **✔**
- Mistral — "**Yes** … stays above **9%**, the regulatory minimum." — **✔**
- Groq — "I don't have enough information in the provided context." — **✘**

### Traps — not in the document (Q10–Q12)

**Q10. RBI's current repo rate?** *(Not in the document)*
- NotebookLM — "Not mentioned; the FSR covers stability indicators, not the policy rate." — **✔**
- Gemini — "Not enough information in the provided context." — **✔**
- Mistral — "Not in the information provided; check the RBI website." — **✔**
- Groq — "I don't have enough information to answer that." — **✔**

**Q11. India's projected GDP growth for 2026-27?** *(Not in the document — only 2025-26 is given)*
- NotebookLM — "No 2026-27 domestic projection; EMDEs 3.9% in CY2026, global 3.0%." — **✔**
- Gemini — "Not enough information for **2026-27**; the data only projects **2025-26 at 6.5%**, and global CY2026 at 3.0% — no India 2026-27 figure." — **✔** *(explicitly refused to reuse 6.5% — the exact trap Mistral fell for)*
- Mistral — "**6.5%**." — **✘** *(hallucination — reused the 2025-26 figure for a year the document never projects)*
- Groq — "I don't have enough information to answer that." — **✔**

**Q12. Exact date the RBI's MPC last met?** *(Not in the document)*
- NotebookLM — "Not specified; the FSR doesn't give MPC meeting dates." — **✔**
- Gemini — "Not enough information; the documents focus on the June 2025 FSR's findings." — **✔**
- Mistral — "I do not have enough information to answer." — **✔**
- Groq — "I don't have that information in the material provided." — **✔**

---

## 3. Results by model

**NotebookLM — 100% (12 / 0 / 0).** The reference, and a clean sweep: every figure exact, and it abstained correctly on all three traps — including naming the *nearby* figures on Q11 (EMDE 3.9%, global 3.0%) without misattributing any of them to India's 2026-27.

**Gemini (Option A) — 100% (12 / 0 / 0).** Full RAG plus the Student persona, and it did both jobs at once: exact figures on every fact and calculation, wrapped in genuinely student-level analogies (the "giant student club," the car slowing from 27 to 11.6 km/h, ₹419 vs ₹466), and a clean sweep of all three traps. The standout is **Q11**: it explicitly refused to reuse the 2025-26 figure (6.5%) for 2026-27 and even separated it from the calendar-2026 global 3.0% — **the exact trap Mistral fell into.** That single question is what puts Gemini a clear notch above Mistral on an otherwise similar run.

**Mistral (Option A) — 91.7% (11 / 0 / 1).** Fast and accurate on all nine substantive questions, with the same figure-preserving discipline as Gemini. Its **one miss is Q11**, a trap: it answered "6.5%" for 2026-27 — the *2025-26* figure reused for a year the document never projects. This is the classic trap failure (confident number instead of an abstention) and is consistent with the recurring hallucination behaviour it showed in earlier tests.

**Groq (TRY 2) — 41.7% (4 / 2 / 6).** A **retrieval failure, not a reasoning failure.** TRY 1 (the app's normal full-context path) couldn't run at all — the context exceeded Groq's 6k-tokens/minute cap (`413`). TRY 2 only fit by trimming to a knowledge-graph-only context (0 prose chunks), so Groq could answer only what the graph had distilled: it got **Q1** (6.5% was a graph node) and gave the right *direction* on Q7/Q8, but **abstained or blanked on every figure that lived only in the report's prose** (Q2–Q6, Q9). Note its three "correct" traps (Q10–Q12) are **blanket abstention**, not genuine calibration — it was abstaining on almost everything.

---

## 4. Key findings

1. **The traps are the separator — and Q11 is the sharpest.** The document projects 2025-26 (6.5%) but *not* 2026-27. NotebookLM, **Gemini**, and Groq all abstained; **Mistral alone hallucinated 6.5%**, its only error. That one question is the entire gap between Gemini (100%) and Mistral (91.7%) — two otherwise near-identical full-RAG runs.
2. **Groq's collapse is about retrieval, not the model.** A large document broke the full-context path outright, and the only way to fit it (KG-only context) starved the model of the prose where most figures lived. This is the strongest evidence yet that **document size + Groq's small TPM budget is the app's real bottleneck**, separate from answer quality.
3. **The persona guardrail held perfectly.** Every substantive answer reproduced the figures exactly (6.5%, 697.9 bn, 2.3%, 15.4 pp, 41.9/46.6, 3.9→5.9, 25.8%, 1.8/1.2, 9%) while being genuinely reworded for a student. "Rewrite the words, never the numbers" worked across two different models.
4. **Full RAG handled a hard, large document well.** On the same pipeline, Gemini (100%) and Mistral (91.7%) both delivered exact, well-explained answers — the failure mode was a single trap, not the substance.
5. **Model choice + retrieval budget dominate.** The spread (100% / 91.7% vs 41.7%) is driven almost entirely by whether the pipeline could deliver the prose to the model, and by trap discipline — not by the models' ability to read the figures when they had them.

---

## 5. Caveats

- **Gemini's run spanned two days** (Q1–Q10 on 19 Aug, Q11–Q12 on 23 Aug) because a full Option-A run exceeds the free-tier 20-requests/day cap. All 12 were answered on the same index; the split is a quota artefact, not a methodology difference.
- **Groq's column is a degraded pipeline** — TRY 1 failed (`413`, document too large for the 6k-TPM free tier); TRY 2 answered from a knowledge-graph-only context (`max_total_tokens=3000`, 0 chunks). It is **not like-for-like** with the full-RAG columns and understates what `gpt-oss-20b` could do with proper retrieval.
- **Persona = Student**, with the numeric guardrail active (which is *why* every model abstains on the traps rather than guessing).
- NotebookLM uses its own retrieval; the app uses LightRAG + local embeddings + the chosen model — so NotebookLM-vs-app is a product comparison, not a pure model comparison.
- One document, one attempt per question. Some judgement in the ◐/✘ calls (e.g. Groq's "25%" on Q7), applied the same way to every model.
- Correct answers are taken from the figures stated in `finance report sample.pdf` (the RBI FSR June 2025 executive summary).
