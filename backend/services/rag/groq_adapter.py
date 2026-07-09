import os

from groq import AsyncGroq

# Groq's free tier caps at 6000 tokens/minute, and LightRAG can burst
# several extraction calls in quick succession (new upload + backlog
# reprocessing). The SDK already retries with backoff on 429s, but its
# default of 2 retries gives up before a per-minute window resets -
# raising it buys more chances to succeed instead of failing outright.
client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    max_retries=5,
)


async def groq_complete(
    prompt: str,
    system_prompt: str = None,
    history_messages=None,
    **kwargs,
):
    """
    Async completion function for LightRAG, backed by Groq.
    """

    messages = []

    if system_prompt:
        messages.append(
            {
                "role": "system",
                "content": system_prompt
            }
        )

    if history_messages:
        messages.extend(history_messages)

    messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0,
        max_tokens=min(kwargs.get("max_tokens", 512), 512),
    )

    content = response.choices[0].message.content

    if content is None:
        return ""

    return str(content).strip()
