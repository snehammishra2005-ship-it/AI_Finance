"""
Web search helper for chat.

Powers the "Search the web" mode: queries Tavily for current sources,
formats them into a citation-numbered prompt for the LLM, and returns a
clean list of the sources so the chat UI can show them Perplexity-style
beneath the answer.
"""

import os
import re
import time
import logging
from collections import OrderedDict
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

# Recency filtering: finance questions about rates/markets/news go stale fast.
# When a query looks time-sensitive, restrict Tavily to recent news so the
# answer reflects the current picture rather than an old cached page.
_RECENCY_HINTS = re.compile(
    r"\b(current|latest|today|now|recent|this (?:week|month|year)|"
    r"20(?:2[4-9]|3\d)|rate|rates|price|prices|stock|stocks|market|markets|"
    r"news|yield|inflation|repo|fed|rbi|forecast|outlook)\b",
    re.IGNORECASE,
)
RECENCY_DAYS = 30

# Domain trust: give authoritative finance/government sources a small ranking
# boost so they're preferred over blogs/forums when relevance is comparable.
_TRUSTED_DOMAINS = (
    "sec.gov", "federalreserve.gov", "imf.org", "worldbank.org", "bis.org",
    "rbi.org.in", "ecb.europa.eu", "treasury.gov", "oecd.org",
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com", "economist.com",
    "investopedia.com", "moneycontrol.com", "morningstar.com",
)
_TRUST_BOOST = 0.15

# Small in-memory cache of recent searches so repeated/identical queries don't
# spend another Tavily credit. Entries expire after CACHE_TTL to avoid serving
# stale results for time-sensitive queries.
_CACHE: "OrderedDict[str, tuple]" = OrderedDict()
_CACHE_MAX = 64
_CACHE_TTL = 600  # seconds (10 min)


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def _is_trusted(url: str) -> bool:
    d = _domain(url)
    return d.endswith(".gov") or any(t in d for t in _TRUSTED_DOMAINS)


def _cache_get(key: str):
    entry = _CACHE.get(key)
    if not entry:
        return None
    ts, value = entry
    if time.time() - ts > _CACHE_TTL:
        _CACHE.pop(key, None)
        return None
    _CACHE.move_to_end(key)
    return value


def _cache_put(key: str, value: dict):
    _CACHE[key] = (time.time(), value)
    _CACHE.move_to_end(key)
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)


def web_search(query: str) -> dict | None:
    """
    Query Tavily for web sources. Returns:
      - None            if no TAVILY_API_KEY is configured
      - {"error": str}  if the request failed
      - {"results": [{"title","url","content","score"}]} on success

    Uses "basic" search depth (1 Tavily credit/query vs 2 for "advanced") and
    does not request Tavily's own answer synthesis - we synthesize ourselves.
    Time-sensitive queries are restricted to recent news; authoritative domains
    get a small ranking boost; and identical recent queries are served from a
    short-lived cache to save Tavily credits.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return None

    cache_key = query.strip().lower()
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": MAX_WEB_RESULTS,
    }
    # Recency filtering for time-sensitive finance queries (rates, markets, news).
    if _RECENCY_HINTS.search(query):
        payload["topic"] = "news"
        payload["days"] = RECENCY_DAYS

    try:
        resp = requests.post(TAVILY_ENDPOINT, json=payload, timeout=WEB_SEARCH_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for r in data.get("results", []):
            if not r.get("url"):
                continue
            url = r["url"].strip()
            base = r.get("score") or 0.0
            results.append({
                "title": (r.get("title") or "").strip(),
                "url": url,
                "content": (r.get("content") or "").strip()[:MAX_WEB_CONTENT_CHARS],
                # Nudge trusted finance/gov domains up the ranking.
                "score": base + (_TRUST_BOOST if _is_trusted(url) else 0.0),
            })

        # Rank by (boosted) relevance and drop weak hits. If filtering would
        # remove everything, keep the best-scoring results so we still answer.
        results.sort(key=lambda r: r["score"], reverse=True)
        strong = [r for r in results if r["score"] >= MIN_RESULT_SCORE]
        results = (strong or results)[:MAX_WEB_RESULTS]

        out = {"results": results}
        _cache_put(cache_key, out)
        return out
    except Exception as e:
        logger.warning(f"Tavily web search failed: {e}")
        return {"error": str(e)}


def iterative_web_search(query: str, refine_fn=None) -> dict | None:
    """
    Bounded "agentic" search: run the initial query, then - if a refine_fn is
    supplied - ask it for ONE follow-up query to fill gaps, search that too,
    and merge the results (deduped by URL, re-ranked). This catches facts the
    first query missed without an unbounded agent loop (at most 2 searches).

    Returns the same shape as web_search. refine_fn(prompt) -> str is expected
    to return a single short search query (or empty to skip the follow-up).
    """
    first = web_search(query)
    if not first or "results" not in first or not first["results"]:
        return first

    if refine_fn is None:
        return first

    titles = "\n".join(f"- {r['title']}" for r in first["results"][:5])
    refine_prompt = (
        "You are refining a web search. Given the user's question and the "
        "titles already found, suggest ONE additional short search query that "
        "would fill an important gap. Reply with ONLY the query text, no "
        "quotes or explanation. If the results already cover it, reply NONE.\n\n"
        f"QUESTION: {query}\n\nTITLES FOUND:\n{titles}"
    )
    try:
        followup = (refine_fn(refine_prompt) or "").strip().strip('"')
    except Exception as e:
        logger.warning(f"Iterative search refine step failed: {e}")
        return first

    if not followup or followup.upper().startswith("NONE") or followup.lower() == query.lower():
        return first

    second = web_search(followup)
    if not second or "results" not in second:
        return first

    # Merge, dedupe by URL, re-rank, cap.
    merged = {r["url"]: r for r in first["results"]}
    for r in second["results"]:
        merged.setdefault(r["url"], r)
    combined = sorted(merged.values(), key=lambda r: r["score"], reverse=True)[:MAX_WEB_RESULTS]
    logger.info(f"Iterative search: follow-up '{followup}' -> {len(combined)} merged sources")
    return {"results": combined}


def _sources_and_block(results: list) -> tuple[list, str]:
    """Shared: turn web results into the UI sources list + a citation-numbered
    text block for the prompt."""
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
    return sources, block


def build_web_prompt(user_message: str, results: list) -> tuple[str, list]:
    """
    Build a citation-numbered prompt from web results and the parallel list
    of sources for the UI.

    Returns (augmented_message, sources) where each source is
    {"n", "title", "url", "domain", "snippet"}.
    """
    sources, block = _sources_and_block(results)
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


def build_blend_prompt(user_message: str, doc_context: str, results: list) -> tuple[str, list]:
    """
    Build a prompt that answers from BOTH the user's uploaded documents and
    live web results in one cited reply (e.g. "compare my statement to current
    rates"). Web sources are cited inline as [1], [2]; the user's own documents
    are referred to in words. Returns (augmented_message, sources).
    """
    sources, block = _sources_and_block(results)
    augmented = (
        "Answer the user's question using BOTH sources below: their uploaded "
        "document(s) and the web search results. Cite web sources inline with "
        "bracketed numbers like [1], [2] that match the numbered results; when "
        "you rely on the user's own documents, refer to them as 'your uploaded "
        "document'. Do not invent sources or facts. If the document and the web "
        "disagree (e.g. different figures), point that out.\n\n"
        f"UPLOADED DOCUMENT CONTEXT:\n{doc_context}\n\n"
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
