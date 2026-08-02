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


def _stream_oai(client, model_id, messages, max_tokens, label):
    """
    Shared streaming generator for OpenAI-style chat clients (OpenAI SDK, Groq
    SDK - both expose the same streamed `choices[].delta.content` shape). Yields
    text chunks as they arrive. Raises LLMProviderError on failure so the engine
    can fall back to another provider (only meaningful before the first chunk).
    """
    try:
        stream = client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0.4,
            max_tokens=max_tokens,
            timeout=REQUEST_TIMEOUT,
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            piece = getattr(delta, "content", None)
            if piece:
                yield piece
    except Exception as e:
        logger.error(f"{label} streaming error: {e}")
        raise LLMProviderError(f"{label}: {e}") from e


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

    def stream_response(self, system_prompt: str, user_message: str, max_tokens: int = 512, history: list = None):
        """
        Yield the response as text chunks. Default implementation degrades
        gracefully to a single chunk (the full non-streamed answer), so a
        provider that doesn't implement real token streaming still works with
        the streaming code path. Providers that support server-side streaming
        override this to yield tokens as they arrive.
        """
        yield self.generate_response(system_prompt, user_message, max_tokens=max_tokens, history=history)


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

    def stream_response(self, system_prompt, user_message, max_tokens=512, history=None):
        yield from _stream_oai(
            self.client, self.model_id,
            _oai_messages(system_prompt, user_message, history),
            max_tokens, "OpenRouter",
        )

# =========================================================
# Gemini Provider
# =========================================================
class GeminiProvider(BaseLLMProvider):
    def __init__(self, model_id: str):
        super().__init__(model_id)

        # Use the current google-genai SDK; the old google.generativeai package
        # is end-of-life (no more updates/fixes).
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        self.client = genai.Client(
            api_key=api_key,
            # SDK timeout is in milliseconds.
            http_options={"timeout": REQUEST_TIMEOUT * 1000},
        )

    def generate_response(self, system_prompt: str, user_message: str, max_tokens: int = 512, history: list = None) -> str:
        from google.genai import types

        try:
            # Native multi-turn: prior turns as user/model contents, with the
            # system prompt passed as a real system_instruction (not concatenated
            # into the user text as the old code did).
            contents = []
            if history:
                for m in history:
                    role = "model" if m.get("role") == "assistant" else "user"
                    contents.append({"role": role, "parts": [{"text": str(m.get("content", ""))}]})
            contents.append({"role": "user", "parts": [{"text": user_message}]})

            # Gemini 3 Flash is a "thinking" model: by default it spends output
            # tokens on internal reasoning, which for short chat budgets can
            # consume the whole allowance and return NO visible text. This is a
            # fast Q&A assistant, so disable thinking to get direct answers (and
            # lower latency). If a model doesn't support disabling it, retry
            # without the thinking_config rather than failing outright.
            def _build_config(disable_thinking: bool):
                kwargs = dict(
                    system_instruction=system_prompt,
                    max_output_tokens=max_tokens,
                    temperature=0.4,
                )
                if disable_thinking:
                    kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
                return types.GenerateContentConfig(**kwargs)

            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=contents,
                    config=_build_config(disable_thinking=True),
                )
            except Exception as think_err:
                if "thinking" not in str(think_err).lower():
                    raise
                logger.info("Gemini model rejected thinking_config; retrying without it.")
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=contents,
                    config=_build_config(disable_thinking=False),
                )

            # The .text accessor raises (or returns None) when the response has
            # no usable text part - e.g. a safety block or a MAX_TOKENS cutoff
            # before any text. Guard it so an empty response degrades to a clean
            # message instead of crashing the request (the old SDK's failure).
            try:
                text = response.text
            except Exception as acc_err:
                logger.warning(f"Gemini .text accessor failed: {acc_err}")
                text = None

            if not text:
                reason = ""
                try:
                    if response.candidates:
                        reason = str(response.candidates[0].finish_reason or "")
                except Exception:
                    pass
                logger.warning(f"Gemini returned no text (finish_reason={reason!r})")
                return (
                    "The model returned an empty response"
                    + (f" (reason: {reason})" if reason else "")
                    + ". Please try rephrasing your question."
                )

            return text.strip()

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

    def stream_response(self, system_prompt, user_message, max_tokens=512, history=None):
        yield from _stream_oai(
            self.client, self.model_id,
            _oai_messages(system_prompt, user_message, history),
            max_tokens, "Groq",
        )


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

    def stream_response(self, system_prompt, user_message, max_tokens=512, history=None):
        yield from _stream_oai(
            self.client, self.model_id,
            _oai_messages(system_prompt, user_message, history),
            max_tokens, self.LABEL,
        )


class CerebrasProvider(_OpenAICompatibleProvider):
    BASE_URL = "https://api.cerebras.ai/v1"
    API_KEY_ENV = "CEREBRAS_API_KEY"
    LABEL = "Cerebras"


class MistralProvider(_OpenAICompatibleProvider):
    BASE_URL = "https://api.mistral.ai/v1"
    API_KEY_ENV = "MISTRAL_API_KEY"
    LABEL = "Mistral"
