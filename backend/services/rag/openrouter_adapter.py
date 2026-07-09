import os
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)


async def gpt55_complete(
    prompt: str,
    system_prompt: str = None,
    history_messages=None,
    **kwargs,
):
    """
    Async completion function for LightRAG.
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
        model="openai/gpt-5.5",
        messages=messages,
        temperature=0,
        max_tokens=min(kwargs.get("max_tokens", 512), 512),
    )

    content = response.choices[0].message.content

    if content is None:
        return ""

    return str(content).strip()
