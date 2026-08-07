import os
import asyncio

from google import genai
from google.genai import types

# Current google-genai SDK (async namespace = client.aio).
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

_TRANSIENT = ("503", "429", "unavailable", "resource_exhausted", "overloaded", "high demand")


async def gemini_complete(
    prompt: str,
    system_prompt: str = None,
    history_messages=None,
    **kwargs,
):
    """
    Async completion function for LightRAG, backed by Gemini 3 Flash.

    Thinking is disabled (thinking_budget=0) so the model spends its token
    budget on the answer, not internal reasoning - important because LightRAG
    caps generation tokens and a thinking model can otherwise return empty.
    Transient 503/429s (free-tier spikes) are retried with backoff.
    """
    contents = []
    if history_messages:
        for m in history_messages:
            role = "model" if m.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": str(m.get("content", ""))}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    cfg = dict(
        max_output_tokens=min(kwargs.get("max_tokens", 512), 512),
        temperature=0,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )
    if system_prompt:
        cfg["system_instruction"] = system_prompt

    last = None
    for attempt in range(4):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-3-flash-preview",
                contents=contents,
                config=types.GenerateContentConfig(**cfg),
            )
            try:
                text = response.text
            except Exception:
                text = None
            return (text or "").strip()
        except Exception as e:
            last = e
            if any(t in str(e).lower() for t in _TRANSIENT) and attempt < 3:
                await asyncio.sleep(10 * (attempt + 1))
                continue
            raise
    raise last
