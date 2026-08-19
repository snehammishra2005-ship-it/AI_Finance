# config/slm_config.py

# NOTE: The first entry is treated as the default model everywhere
# (LLMEngine falls back to SLM_LIST[0], and the UI selects it when the
# user hasn't picked one). Groq is kept first because it's the reliably
# working provider.
SLM_LIST = [
    {
        "name": "GPT-OSS 20B (Groq)",
        "model_id": "openai/gpt-oss-20b",
        "provider": "groq",
        "description": "Fast Groq-hosted GPT-OSS 20B (replaces the retired Llama 3.1 8B Instant)."
    },
    {
        "name": "GPT-5.5 (OpenRouter)",
        "model_id": "openai/gpt-5.5",
        "provider": "openrouter",
        "description": "GPT-5.5 via OpenRouter"
    },
    {
        "name": "Gemini 3 Flash (Google)",
        "provider": "google",
        "model_id": "gemini-3-flash-preview",
        "description": "Fast multimodal model from Google"
    },
    {
        "name": "Claude 3 Haiku (Anthropic)",
        "provider": "anthropic",
        "model_id": "claude-3-haiku-20240307",
        "description": "Fast and responsive model from Anthropic"
    },
    {
        "name": "GPT-OSS 120B (Cerebras)",
        "provider": "cerebras",
        "model_id": "gpt-oss-120b",
        "description": "GPT-OSS 120B on Cerebras - very fast inference (free tier)"
    },
    {
        "name": "Mistral Small (Mistral)",
        "provider": "mistral",
        "model_id": "mistral-small-latest",
        "description": "Mistral Small via La Plateforme (free tier)"
    }
]
