# config/slm_config.py

# NOTE: The first entry is treated as the default model everywhere
# (LLMEngine falls back to SLM_LIST[0], and the UI selects it when the
# user hasn't picked one). Groq is kept first because it's the reliably
# working provider.
SLM_LIST = [
    {
        "name": "Llama 3.1 8B Instant (Groq)",
        "model_id": "llama-3.1-8b-instant",
        "provider": "groq",
        "description": "Ultra-fast Groq-hosted Llama model."
    },
    {
        "name": "GPT-5.5 (OpenRouter)",
        "model_id": "openai/gpt-5.5",
        "provider": "openrouter",
        "description": "GPT-5.5 via OpenRouter"
    },
    {
        "name": "Gemini 1.5 Flash (Google)",
        "provider": "google",
        "model_id": "gemini-1.5-flash",
        "description": "Fast multimodal model from Google"
    },
    {
        "name": "Claude 3 Haiku (Anthropic)",
        "provider": "anthropic",
        "model_id": "claude-3-haiku-20240307",
        "description": "Fast and responsive model from Anthropic"
    }
]
