"""
Finance-specific metric extraction.

Reads a document's extracted text (including the pipe-formatted tables the
file processor now preserves) and pulls out the financial metrics that are
explicitly stated - revenue, profit, margins, ratios, etc. - as structured
rows. LLM-based because financial documents vary too much (synonyms, units,
layouts) for reliable regex; never fabricates numbers.
"""

import re
import json
import logging

from backend.services.rag.groq_adapter import client as groq_client

logger = logging.getLogger(__name__)

MODEL = "llama-3.1-8b-instant"

# Cap input so a single call stays within Groq's free-tier tokens-per-minute
# limit. Large reports are only analysed from the start (documented limitation).
MAX_TEXT_CHARS = 8000
MAX_TOKENS = 1500


async def extract_financial_metrics(text: str) -> dict:
    """
    Extract explicitly-stated financial metrics from a document.

    Returns:
      {
        "metrics": [{"name", "value", "unit", "period"}],
        "currency": str | None,
        "note": str | None,   # explanation when metrics is empty
      }
    Never invents metrics: returns an empty list on no-content, parse failure,
    or LLM error.
    """
    snippet = (text or "").strip()[:MAX_TEXT_CHARS]
    if not snippet:
        return {"metrics": [], "currency": None, "note": "No text to analyze."}

    prompt = (
        "You are a financial analyst. From the document below, extract the key "
        "financial metrics that are EXPLICITLY stated - for example revenue / "
        "turnover, net profit, operating profit or EBITDA, gross/operating/net "
        "margin, EPS, total assets, liabilities, debt, cash, growth rates, and "
        "key ratios. For each metric give its name, numeric value, unit or "
        "currency, and the period or context it refers to. Do NOT infer, "
        "calculate, or invent metrics that are not stated in the text.\n\n"
        "Return ONLY a JSON object, no other text, in exactly this form:\n"
        '{"currency": "<main currency, or null>", "metrics": ['
        '{"name": "...", "value": "...", "unit": "...", "period": "..."}]}\n'
        "If no financial metrics are present, return "
        '{"currency": null, "metrics": []}.\n\n'
        f"DOCUMENT:\n{snippet}"
    )

    try:
        resp = await groq_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=MAX_TOKENS,
        )
        raw = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.error(f"Metric extraction LLM call failed: {e}")
        return {"metrics": [], "currency": None, "note": f"Extraction failed: {e}"}

    parsed = _parse_metrics(raw)
    if parsed is None:
        return {
            "metrics": [],
            "currency": None,
            "note": "Could not parse metrics from the model response.",
        }
    return parsed


def _parse_metrics(raw: str):
    """Extract the JSON object from the model response (tolerant of surrounding
    prose) and normalize it. Returns None if it can't be parsed."""
    if not raw:
        return None

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None

    try:
        data = json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return None

    metrics = []
    for item in data.get("metrics", []) or []:
        if not isinstance(item, dict):
            continue
        row = {
            "name": str(item.get("name", "")).strip(),
            "value": str(item.get("value", "")).strip(),
            "unit": str(item.get("unit", "")).strip(),
            "period": str(item.get("period", "")).strip(),
        }
        if row["name"] and row["value"]:
            metrics.append(row)

    currency = data.get("currency")
    currency = str(currency).strip() if currency else None

    return {
        "metrics": metrics,
        "currency": currency,
        "note": None if metrics else "No financial metrics were found in the document.",
    }
