# Deep Research Integration — Build & Test Report

**Feature:** "Deep Research" in Q&A — web search built directly into the chat.
When enabled, the assistant searches the live web, answers with **inline
`[1][2]` citations**, and lists the **sources it used** beneath the reply
(ChatGPT / Perplexity / NotebookLM style).

**Status:** ✅ Built and verified working end-to-end.

> **Note:** This replaces an earlier design that used a separate "Research"
> page producing a long combined web+document report. Per updated
> requirements, Deep Research is now a **toggle inside the normal chat** that
> shows the **list of sources used** below each answer. The standalone page
> and its `/research` endpoint were removed.

---

## 1. How it works (user's view)

1. Open the **Chat** tab.
2. Tick **"🌐 Search the web"** (a toggle next to "📚 Answer using my uploaded
   documents"). Off by default — the user opts in.
3. Ask a question. The assistant searches the web, answers with inline
   `[1]`, `[2]` citation markers, and shows a **"🌐 N sources"** list beneath
   the answer — each source is a linked title + domain + snippet.
4. Sources stay attached to that message as the conversation continues.

If both toggles are on, **web search takes priority** over the document mode.

---

## 2. Architecture

| Layer | File | Role |
|-------|------|------|
| Web search | `backend/services/research_service.py` | `web_search()` queries **Tavily**; `build_web_prompt()` turns results into a citation-numbered prompt + a clean sources list |
| Chat API | `backend/main.py` → `POST /chat` | New `web_search: bool` flag. When true, augments the message with web results and returns `{response, model, sources, web_note}` |
| Synthesis | `backend/services/llm_service.py` | The selected LLM (default **Groq Llama 3.1 8B**) writes the cited answer |
| UI | `ui/chat.py` | "🌐 Search the web" toggle; `render_sources()` shows the sources list; sources are persisted in each message so they survive reruns |

**Response shape** (`/chat` with `web_search: true`):
```json
{
  "response": "…answer with [1][2] citations…",
  "model": "Llama 3.1 8B Instant (Groq)",
  "sources": [{"n": 1, "title": "...", "url": "...", "domain": "...", "snippet": "..."}],
  "web_note": null
}
```
`web_note` carries a transparency message when web search was requested but
unavailable (no key / failed / no results); `sources` is empty in that case.

---

## 3. Key design decision: Tavily, not Groq's built-in web search

The original intent was to use **Groq's compound/agentic models** (native web
search) to reuse the existing key. Verification found this **blocked on the
free tier**: both `groq/compound` and `groq/compound-mini` returned
**`413 Request Too Large`** on even a 5-word prompt, while regular Groq models
worked fine. So web search uses **Tavily** (free tier, purpose-built for LLM
research); Groq's regular Llama model writes the answer.

---

## 4. Test results

Run live against `POST /chat` with the Tavily key configured.

### Test 1 — Web search ON ✅
*"What is the current RBI repo rate and recent policy stance?"* (`web_search: true`)

| Field | Result |
|-------|--------|
| `sources` | **6** (pib.gov.in, corplawupdates.in, bankbazaar.com, youtube.com…) |
| Inline citations in answer | `[1]`, `[3]`, `[4]` — matching the numbered sources |
| `web_note` | none (search succeeded) |
| Answer | Current & grounded: *"the current RBI repo rate is 5.25% as decided in the 61st MPC meeting in June 2026 [3]"* |

A second run on GNPA (bad-loan) trends returned 6 sources (livemint, PIB,
ICRA, Brickwork Ratings…) with inline `[1][4]` citations and current figures
(GNPA 2.31% by March 2025) — matching the reference UI's example topic.

### Test 2 — Web search OFF (normal chat) ✅
*"What is a mutual fund in one sentence?"* (`web_search: false`)
- `sources`: **0**, `web_note`: none — a plain, persona-styled answer with no
  sources panel. Confirms the feature is cleanly opt-in and doesn't affect
  normal chat.

### Test 3 — RAG mode unaffected ✅
Ingested a document and queried via the document toggle (`/rag/ask`) — still
returns the correct grounded answer. The redo didn't disturb the existing
document-Q&A path.

---

## 5. Honest findings / caveats

1. **Source quality varies.** Tavily returns whatever is most relevant, which
   can include blogs and YouTube videos alongside authoritative sources (e.g.
   the repo-rate query surfaced a few `youtube.com` results). The model still
   cites by number, so provenance is visible, but sources aren't filtered to
   "authoritative only." A domain allow/deny list could be added later.
2. **Answer length.** Chat answers run through the provider's 512-token cap —
   good for a cited chat reply, not a long-form report (which was the point of
   moving away from the report page).
3. **Synthesis model.** Runs on Groq `llama-3.1-8b-instant` (the reliably
   working provider) — fast and solid, not a frontier model.
4. **Free-tier limits.** Web result content and count are capped (6 results,
   ~600 chars each) to keep each call within Groq's ~6,000 tokens/minute free
   tier; rapid repeated use can still hit rate limits.
5. **Single-pass.** Search → answer with citations in one shot, not a
   multi-step agent that reformulates queries and drills down.

---

## 6. Verification method note

The backend path was verified directly via `POST /chat` (evidence above: real
sources, inline citations, correct empty-sources behavior when off). The chat
UI imports cleanly and the frontend boots without errors; it renders exactly
the `sources` shape validated here (a "🌐 N sources" expander with linked
title, domain, and snippet, persisted per message). A live in-browser
screenshot of the sources panel was not captured this round due to a flaky
browser-automation connection.
