from backend.services.llm_service import llm_engine


async def gpt55_complete(
    prompt: str,
    system_prompt=None,
    history_messages=None,
    **kwargs,
):
    """
    LightRAG LLM Adapter
    """

    full_prompt = ""

    if system_prompt:
        full_prompt += system_prompt + "\n\n"

    full_prompt += prompt

    return llm_engine.generate_response(
        message=full_prompt,
        persona="General Assistant"
    )