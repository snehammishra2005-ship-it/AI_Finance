import os
import logging

logger = logging.getLogger(__name__)

# Per-request timeout (seconds) for all synchronous provider API calls, so a
# hung upstream can't block a request/worker indefinitely.
REQUEST_TIMEOUT = 60


def _oai_messages(system_prompt: str, user_message: str, history=None) -> list:
    """
    Assemble OpenAI-style chat messages: the system prompt, any prior
    conversation turns, then the current user message. `history` is a list of
    {"role": "user"|"assistant", "content": str}; None/empty means single-turn
    (unchanged behaviour).
    """
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages


class LLMProviderError(Exception):
    """
    Raised when a provider's API call fails (bad key, rate limit, timeout,
    upstream error). Callers should surface this as a real error rather than
    letting the failure text be mistaken for a successful answer.
    """


class BaseLLMProvider:
    """Base class for all LLM providers."""
    def __init__(self, model_id: str):
        self.model_id = model_id

    def generate_response(self, system_prompt: str, user_message: str, max_tokens: int = 512, history: list = None) -> str:
        raise NotImplementedError("Subclasses must implement generate_response")


# =========================================================
# OpenRouter Provider
# =========================================================
class OpenRouterProvider(BaseLLMProvider):

    def __init__(self, model_id: str):
        super().__init__(model_id)

        from openai import OpenAI

        api_key = os.environ.get(
            "OPENROUTER_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set"
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 512,
        history: list = None
    ) -> str:

        try:

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=_oai_messages(system_prompt, user_message, history),
                temperature=0.4,
                max_tokens=max_tokens,
                timeout=REQUEST_TIMEOUT
            )

            content = response.choices[0].message.content

            if content is None:

                logger.warning(
                    f"OpenRouter returned empty content for model {self.model_id}"
                )

                return (
                    "The model returned an empty response. "
                    "Please try another prompt."
                )

            return str(content).strip()

        except Exception as e:

            logger.error(
                f"OpenRouter API Error: {e}"
            )

            raise LLMProviderError(f"OpenRouter: {e}") from e

# =========================================================
# Gemini Provider
# =========================================================
class GeminiProvider(BaseLLMProvider):
    def __init__(self, model_id: str):
        super().__init__(model_id)

        import google.generativeai as genai

        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(model_name=self.model_id)

    def generate_response(self, system_prompt: str, user_message: str, max_tokens: int = 512, history: list = None) -> str:
        try:
            convo = ""
            if history:
                for m in history:
                    who = "User" if m.get("role") == "user" else "Assistant"
                    convo += f"{who}: {m.get('content', '')}\n"

            combined_prompt = (
                f"System Instructions:\n{system_prompt}\n\n"
                f"{convo}"
                f"User Message:\n{user_message}"
            )

            response = self.model.generate_content(
                combined_prompt,
                generation_config={"max_output_tokens": max_tokens, "temperature": 0.4},
                request_options={"timeout": REQUEST_TIMEOUT}
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            raise LLMProviderError(f"Gemini: {e}") from e


# =========================================================
# Groq Provider
# =========================================================
class GroqProvider(BaseLLMProvider):
    def __init__(self, model_id: str):
        super().__init__(model_id)

        from groq import Groq

        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")

        self.client = Groq(api_key=api_key)

    def generate_response(self, system_prompt: str, user_message: str, max_tokens: int = 512, history: list = None) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=_oai_messages(system_prompt, user_message, history),
                max_tokens=max_tokens,
                temperature=0.4,
                timeout=REQUEST_TIMEOUT
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Groq API Error: {e}")
            raise LLMProviderError(f"Groq: {e}") from e


# =========================================================
# Anthropic Provider
# =========================================================
class AnthropicProvider(BaseLLMProvider):
    def __init__(self, model_id: str):
        super().__init__(model_id)

        from anthropic import Anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

        self.client = Anthropic(api_key=api_key)

    def generate_response(self, system_prompt: str, user_message: str, max_tokens: int = 512, history: list = None) -> str:
        try:
            a_messages = list(history) if history else []
            a_messages.append({"role": "user", "content": user_message})

            response = self.client.messages.create(
                model=self.model_id,
                system=system_prompt,
                max_tokens=max_tokens,
                messages=a_messages,
                temperature=0.4,
                timeout=REQUEST_TIMEOUT
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Anthropic API Error: {e}")
            raise LLMProviderError(f"Anthropic: {e}") from e


# =========================================================
# OpenAI-compatible providers (Cerebras, Mistral)
# =========================================================
class _OpenAICompatibleProvider(BaseLLMProvider):
    """
    Shared implementation for providers that expose an OpenAI-compatible chat
    completions API - only the base URL and API-key env var differ. Cerebras
    and Mistral both work this way, so they reuse the already-present `openai`
    client instead of pulling in a vendor SDK.
    """

    BASE_URL = None
    API_KEY_ENV = None
    LABEL = "provider"

    def __init__(self, model_id: str):
        super().__init__(model_id)

        from openai import OpenAI

        api_key = os.environ.get(self.API_KEY_ENV)
        if not api_key:
            raise ValueError(f"{self.API_KEY_ENV} environment variable is not set")

        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)

    def generate_response(self, system_prompt: str, user_message: str, max_tokens: int = 512, history: list = None) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=_oai_messages(system_prompt, user_message, history),
                temperature=0.4,
                max_tokens=max_tokens,
                timeout=REQUEST_TIMEOUT,
            )

            content = response.choices[0].message.content

            if content is None:
                logger.warning(
                    f"{self.LABEL} returned empty content for model {self.model_id}"
                )
                return (
                    "The model returned an empty response. "
                    "Please try another prompt."
                )

            return str(content).strip()

        except Exception as e:
            logger.error(f"{self.LABEL} API Error: {e}")
            raise LLMProviderError(f"{self.LABEL}: {e}") from e


class CerebrasProvider(_OpenAICompatibleProvider):
    BASE_URL = "https://api.cerebras.ai/v1"
    API_KEY_ENV = "CEREBRAS_API_KEY"
    LABEL = "Cerebras"


class MistralProvider(_OpenAICompatibleProvider):
    BASE_URL = "https://api.mistral.ai/v1"
    API_KEY_ENV = "MISTRAL_API_KEY"
    LABEL = "Mistral"
