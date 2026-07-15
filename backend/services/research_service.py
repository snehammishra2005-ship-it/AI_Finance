"""
Web search helper for chat.

Powers the "Search the web" mode: queries Tavily for current sources,
formats them into a citation-numbered prompt for the LLM, and returns a
clean list of the sources so the chat UI can show them Perplexity-style
beneath the answer.
"""

import os
import logging
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

TAVILY_ENDPOINT = "https://api.tavily.com/search"

MAX_WEB_RESULTS = 6
MAX_WEB_CONTENT_CHARS = 600
MAX_SNIPPET_CHARS = 220


def web_search(query: str) -> dict | None:
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
                    "title": (r.get("title") or "").strip(),
                    "url": (r.get("url") or "").strip(),
                    "content": (r.get("content") or "").strip()[:MAX_WEB_CONTENT_CHARS],
                }
                for r in data.get("results", [])[:MAX_WEB_RESULTS]
                if r.get("url")
            ],
        }
    except Exception as e:
        logger.warning(f"Tavily web search failed: {e}")
        return {"error": str(e)}


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def build_web_prompt(user_message: str, results: list) -> tuple[str, list]:
    """
    Build a citation-numbered prompt from web results and the parallel list
    of sources for the UI.

    Returns (augmented_message, sources) where each source is
    {"n", "title", "url", "domain", "snippet"}.
    """
    sources = []
    block = ""

    for i, r in enumerate(results, 1):
        sources.append({
            "n": i,
            "title": r["title"] or r["url"],
            "url": r["url"],
            "domain": _domain(r["url"]),
            "snippet": r["content"][:MAX_SNIPPET_CHARS],
        })
        block += f"[{i}] {r['title']} — {r['url']}\n{r['content']}\n\n"

    augmented = (
        "Answer the user's question using the web search results below. "
        "Cite the sources you use inline with bracketed numbers like [1], [2] "
        "that match the numbered results. Only cite sources you actually rely "
        "on, and do not invent sources or facts. If the results do not answer "
        "the question, say so.\n\n"
        f"WEB SEARCH RESULTS:\n{block}\n"
        f"QUESTION: {user_message}"
    )
    return augmented, sources
