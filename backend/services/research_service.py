"""
Deep Research service.

Combines live web search (Tavily) with the user's uploaded documents
(per-session LightRAG) and synthesizes a single cited research report via
Groq. Every part degrades gracefully: if the Tavily key is missing the
report is built from documents + model knowledge; if the session has no
documents it relies on the web; if neither is available it answers from the
model's own knowledge and says so.
"""

import os
import asyncio
import logging

import requests
from lightrag import QueryParam

from backend.services.rag.rag_service import rag_service_manager
from backend.services.rag.groq_adapter import client as groq_client

logger = logging.getLogger(__name__)

TAVILY_ENDPOINT = "https://api.tavily.com/search"

# Synthesis model + budget. Research reports need more room than a normal
# chat reply (providers cap those at 512), but input is capped below to stay
# within Groq's free-tier tokens-per-minute limit.
SYNTHESIS_MODEL = "llama-3.1-8b-instant"
SYNTHESIS_MAX_TOKENS = 1500

# Input caps (characters) so a single synthesis call stays within TPM limits.
MAX_WEB_RESULTS = 4
MAX_WEB_CONTENT_CHARS = 600
MAX_DOC_CONTEXT_CHARS = 2500


def _web_search(query: str) -> dict | None:
    """
    Query Tavily for web sources. Returns:
      - None            if no TAVILY_API_KEY is configured
      - {"error": str}  if the request failed
      - {"answer": str, "results": [{"title","url","content"}]} on success
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return None

    try:
        resp = requests.post(
            TAVILY_ENDPOINT,
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": MAX_WEB_RESULTS,
                "include_answer": True,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "answer": (data.get("answer") or "").strip(),
            "results": [
                {
                    "title": r.get("title", "") or "",
                    "url": r.get("url", "") or "",
                    "content": (r.get("content", "") or "")[:MAX_WEB_CONTENT_CHARS],
                }
                for r in data.get("results", [])[:MAX_WEB_RESULTS]
            ],
        }
    except Exception as e:
        logger.warning(f"Tavily web search failed: {e}")
        return {"error": str(e)}


async def _doc_context(session_id: str, query: str) -> str:
    """Retrieve raw retrieval context from the session's uploaded documents
    (no synthesis LLM call). Returns '' if none or on error."""
    try:
        svc = await rag_service_manager.get(session_id)
        await svc.initialize()
        ctx = await svc.rag.aquery(
            query,
            param=QueryParam(mode="mix", only_need_context=True),
        )
        ctx = (ctx or "").strip()
        # Guard against LightRAG's "no context" sentinel responses.
        if not ctx or "[no-context]" in ctx.lower():
            return ""
        return ctx[:MAX_DOC_CONTEXT_CHARS]
    except Exception as e:
        logger.warning(f"Doc context retrieval failed for session {session_id}: {e}")
        return ""


def _build_prompt(question: str, web: dict | None, doc_ctx: str) -> tuple[str, list]:
    """Assemble the synthesis prompt and the list of web sources used."""
    web_results = web["results"] if (web and "error" not in web) else []

    web_block = ""
    if web and "error" not in web and web.get("answer"):
        web_block += f"Web overview: {web['answer']}\n\n"
    for i, r in enumerate(web_results, 1):
        web_block += f"[W{i}] {r['title']} — {r['url']}\n{r['content']}\n\n"

    prompt = (
        "You are a financial research assistant. Using ONLY the sources below, "
        "write a thorough, well-structured research answer to the question. Use "
        "clear headings and bullet points where helpful. Cite web sources inline "
        "as [W1], [W2] matching the numbered items, and cite the user's uploaded "
        "documents as [Docs] when you use them. If the sources conflict or are "
        "insufficient, say so plainly. Do not invent facts, numbers, or citations.\n\n"
        f"QUESTION:\n{question}\n\n"
        f"=== WEB SOURCES ===\n{web_block or '(no web sources available)'}\n\n"
        f"=== UPLOADED DOCUMENTS ===\n{doc_ctx or '(no relevant uploaded documents)'}\n\n"
        "Write the research answer now."
    )
    return prompt, web_results


async def deep_research(question: str, session_id: str, persona: str = "General User") -> dict:
    """
    Run web + document research and synthesize a cited report.

    Returns:
      {
        "report": str,
        "web_sources": [{"title","url"}],
        "web_configured": bool,   # Tavily key present and search succeeded
        "used_docs": bool,        # uploaded-document context was used
        "notes": [str],           # transparency notes about missing sources
      }
    """
    # Run web search (blocking requests) off the event loop, and doc
    # retrieval concurrently.
    web_task = asyncio.to_thread(_web_search, question)
    doc_task = _doc_context(session_id, question)
    web, doc_ctx = await asyncio.gather(web_task, doc_task)

    notes = []
    if web is None:
        notes.append("Web search is not configured (no TAVILY_API_KEY set), so this answer does not include live web sources.")
    elif "error" in web:
        notes.append("Web search failed for this query; answer is based on uploaded documents and model knowledge only.")
    if not doc_ctx:
        notes.append("No relevant content was found in your uploaded documents for this question.")

    prompt, web_results = _build_prompt(question, web, doc_ctx)

    from utils.persona_manager import get_persona_prompt
    persona_instructions = get_persona_prompt(persona)
    system_prompt = (
        "You are a helpful financial research assistant. "
        f"{persona_instructions}"
    )

    try:
        resp = await groq_client.chat.completions.create(
            model=SYNTHESIS_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=SYNTHESIS_MAX_TOKENS,
        )
        report = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.error(f"Research synthesis failed: {e}")
        report = f"⚠️ Research synthesis failed: {e}"

    return {
        "report": report,
        "web_sources": [{"title": r["title"], "url": r["url"]} for r in web_results],
        "web_configured": bool(web) and "error" not in web,
        "used_docs": bool(doc_ctx),
        "notes": notes,
    }
