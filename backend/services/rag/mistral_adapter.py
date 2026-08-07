import os

from openai import AsyncOpenAI

# Mistral exposes an OpenAI-compatible API, so we reuse the openai client
# pointed at Mistral's base URL. Retries help ride out transient rate limits
# during LightRAG's burst of entity-extraction calls at index time.
client = AsyncOpenAI(
    api_key=os.getenv("MISTRAL_API_KEY"),
    base_url="https://api.mistral.ai/v1",
    max_retries=5,
)


async def mistral_complete(
    prompt: str,
    system_prompt: str = None,
    history_messages=None,
    **kwargs,
):
    """Async completion function for LightRAG, backed by Mistral Small."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history_messages:
        messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model="mistral-small-latest",
        messages=messages,
        temperature=0,
        max_tokens=min(kwargs.get("max_tokens", 512), 512),
    )

    content = response.choices[0].message.content
    return str(content).strip() if content else ""
