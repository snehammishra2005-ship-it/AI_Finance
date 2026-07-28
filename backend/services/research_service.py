"""
Web search helper for chat.

Powers the "Search the web" mode: queries Tavily for current sources,
formats them into a citation-numbered prompt for the LLM, and returns a
clean list of the sources so the chat UI can show them Perplexity-style
beneath the answer.
"""

import os
import re
import logging
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

TAVILY_ENDPOINT = "https://api.tavily.com/search"

MAX_WEB_RESULTS = 6
MAX_WEB_CONTENT_CHARS = 600
MAX_SNIPPET_CHARS = 220

# Tavily returns a 0-1 relevance score per result; drop clearly-irrelevant
# hits so weak/spammy sources don't get cited in a finance answer.
MIN_RESULT_SCORE = 0.3

# Tavily usually answers in a few seconds. Keep this tight so a slow search
# plus the LLM synthesis (up to REQUEST_TIMEOUT=60s) stays comfortably under
# the UI's 120s client budget instead of racing it.
WEB_SEARCH_TIMEOUT = 15


def web_search(query: str) -> dict | None:
    """
    Query Tavily for web sources. Returns:
      - None            if no TAVILY_API_KEY is configured
      - {"error": str}  if the request failed
      - {"results": [{"title","url","content","score"}]} on success

    Uses "basic" search depth (1 Tavily credit/query vs 2 for "advanced") and
    does not request Tavily's own answer synthesis - we synthesize from the
    raw results ourselves, so paying for a server-side answer we discard would
    only add latency.
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
                "search_depth": "basic",
                "max_results": MAX_WEB_RESULTS,
            },
            timeout=WEB_SEARCH_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        results = [
            {
                "title": (r.get("title") or "").strip(),
                "url": (r.get("url") or "").strip(),
                "content": (r.get("content") or "").strip()[:MAX_WEB_CONTENT_CHARS],
                "score": r.get("score") or 0.0,
            }
            for r in data.get("results", [])
            if r.get("url")
        ]

        # Rank by relevance and drop weak hits. If filtering would remove
        # everything, keep the best-scoring results so we still answer rather
        # than silently falling back to a no-web response.
        results.sort(key=lambda r: r["score"], reverse=True)
        strong = [r for r in results if r["score"] >= MIN_RESULT_SCORE]
        results = (strong or results)[:MAX_WEB_RESULTS]

        return {"results": results}
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


def strip_invalid_citations(text: str, num_sources: int) -> str:
    """
    Remove inline [n] citation markers that point past the number of sources
    actually shown, so the user never sees a citation like [7] with no
    matching entry in the sources list. Leaves valid [1..num_sources] intact.
    """
    if not text:
        return text

    def _keep(match):
        n = int(match.group(1))
        return match.group(0) if 1 <= n <= num_sources else ""

    return re.sub(r"\[(\d+)\]", _keep, text)
