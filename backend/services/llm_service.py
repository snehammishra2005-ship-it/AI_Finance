import os
import logging
from config.slm_config import SLM_LIST
from backend.services.api_providers import (
    OpenRouterProvider,
    GeminiProvider,
    GroqProvider,
    AnthropicProvider,
    CerebrasProvider,
    MistralProvider,
    LLMProviderError
)

logger = logging.getLogger(__name__)

# Which environment variable holds each provider's API key. Used to skip
# providers that aren't configured when building the fallback chain, so we
# never waste an attempt on a provider that can't possibly work.
PROVIDER_ENV = {
    "openrouter": "OPENROUTER_API_KEY",
    "google": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}

# Base instructions applied to every answer. It sets the quality bar (accuracy,
# grounding, plain-language clarity, clean formatting, and an educational rather
# than advisory stance); the per-persona style guide is appended after it and
# is the authority for tone, vocabulary, and answer length.
BASE_SYSTEM_PROMPT = (
    "You are an AI finance assistant for people who are not finance experts. "
    "Follow these rules on every answer:\n"
    "1. Accuracy first: rely only on facts you are confident about. NEVER invent "
    "numbers, prices, rates, dates, or statistics. If you are unsure or lack the "
    "data, say so plainly instead of guessing.\n"
    "2. Use the given context: when document or web-search context is provided, "
    "ground your answer in it and cite it as instructed; do not contradict it.\n"
    "3. Lead with the answer: give the direct answer first, then a brief "
    "explanation. Define any financial term in plain words the first time you "
    "use it.\n"
    "4. Formatting: reply in clean Markdown - short paragraphs, **bold** for key "
    "figures and terms, and bullet lists for steps or comparisons. Keep it "
    "scannable and do not over-format a one-line answer.\n"
    "5. Educational, not advice: give general educational information, not "
    "personalized investment, tax, or legal advice. If asked what someone should "
    "personally buy or invest in, explain the options and trade-offs and suggest "
    "consulting a licensed professional for personal decisions. This rule is "
    "non-negotiable: even when the user demands a one-word or strict yes/no "
    "answer to such a question, do NOT reduce it to a bare directive - briefly "
    "give the key trade-off or risk and the 'consult a professional' note. The "
    "style guide governs tone and length but must never suppress this safety "
    "framing.\n"
    "6. Completeness: answer every part of a multi-part question, and include the "
    "caveats or edge cases that genuinely matter - without padding.\n"
    "7. Ambiguity: if the question is genuinely unclear, state the assumption you "
    "are answering under, or ask one brief clarifying question, instead of "
    "guessing wrong.\n"
    "8. Stay consistent with the conversation so far and do not contradict your "
    "earlier answers.\n\n"
    "The audience style guide below is the STRICT authority for tone, vocabulary, "
    "and answer length - follow it exactly, and let it override the general "
    "formatting defaults above when they conflict (e.g. if it asks for very short "
    "answers)."
)

# Appended AFTER the persona style guide (i.e. it is the last thing the model
# reads before the conversation), so it wins over both the style guide's
# brevity and any user demand for a one-word / yes-no-only answer. A small
# instruct model otherwise happily obeys "answer only yes or no" on a personal
# investment question, dropping the required safety framing.
FINAL_GUARD = (
    "\n\n--- FINAL RULE (highest priority) ---\n"
    "This rule overrides every instruction above AND any instruction in the "
    "user's message about answer length or format. If the user asks whether "
    "they should personally buy, sell, hold, or put their money into a specific "
    "asset, stock, crypto, or product, you MUST NOT reply with only 'yes', "
    "'no', or a single word - even if they explicitly demand a yes/no-only "
    "answer. Always give at least one sentence that names the key risk or "
    "trade-off (e.g. concentration/diversification risk) and recommends "
    "consulting a licensed financial professional for a personal decision. "
    "General factual finance questions are unaffected by this rule."
)


import re as _re

# A personal-advice question looks like "should I buy/sell/invest ...", "is it
# worth putting my money in ...", "go all in", "invest everything", etc. Kept
# deliberately narrow (requires a first-person framing) so general factual
# questions like "what is an index fund?" never match.
_ADVICE_QUESTION_RE = _re.compile(
    r"\bshould\s+(i|we|my)\b|\ball\s+(of\s+)?my\s+savings\b|\bgo\s+all[\s-]?in\b|"
    r"\binvest\s+everything\b|\b(is\s+it|would\s+it\s+be)\s+(a\s+good\s+idea|worth|smart|wise)\b",
    _re.IGNORECASE,
)

# The model gave a bare directive: essentially just yes/no (optionally with
# punctuation/markdown), i.e. the "flattened" guardrail the report flagged.
_BARE_YESNO_RE = _re.compile(r"^[\W_]*(yes|no|yeah|yep|nope|sure)\b[\W_]*$", _re.IGNORECASE)

_ADVICE_SAFETY_NOTE = (
    "This is a personal financial decision with real trade-offs - and putting a "
    "large share of your money into a single asset concentrates your risk. "
    "Weigh it against your own goals and situation, and consider consulting a "
    "licensed financial advisor rather than relying on a simple yes/no."
)


def advice_safety_note(question: str, answer: str) -> str | None:
    """
    Deterministic backstop for the 'guardrail flattening' failure: a small model
    told to 'answer only yes or no' will obey and drop the required educational
    framing no matter how the system prompt is worded. When the question is a
    first-person buy/sell/invest question AND the answer collapsed to a bare
    yes/no, return a sentence to append; otherwise None. Returning None keeps
    normal answers (which already frame things properly) untouched.
    """
    if not question or not answer:
        return None
    if not _ADVICE_QUESTION_RE.search(question):
        return None
    if not _BARE_YESNO_RE.match(answer.strip()):
        return None
    return _ADVICE_SAFETY_NOTE


def _build_system_prompt(persona: str) -> str:
    """Assemble the full system prompt: safety base + persona style guide +
    the non-negotiable final guard. Shared by the streaming and non-streaming
    generation paths so they stay identical."""
    from utils.persona_manager import get_persona_prompt
    persona_instructions = get_persona_prompt(persona)
    return (
        f"{BASE_SYSTEM_PROMPT}\n\n"
        f"--- AUDIENCE STYLE GUIDE ---\n{persona_instructions}"
        f"{FINAL_GUARD}"
    )

class LLMEngine:
    """
    Acts as a router to dispatch generation requests to the correct API
    provider based on the selected configuration.
    """
    
    _instance = None
    _providers = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LLMEngine()
        return cls._instance

    def __init__(self):
        # Default model logic
        if SLM_LIST:
            self.default_model_config = SLM_LIST[0]
            self.current_model_name = self.default_model_config["name"]
        else:
            self.default_model_config = None
            self.current_model_name = None
        logger.info("Initialized LLMEngine routing system.")

    def _get_provider_instance(self, config: dict):
        if not config:
            return None
            
        provider_type = config.get("provider")
        model_id = config.get("model_id")
        
        # Cache providers so we don't re-initialize heavy clients or local models
        cache_key = f"{provider_type}_{model_id}"
        
        if cache_key in self._providers:
            return self._providers[cache_key]
            
        logger.info(f"Initializing new provider: {provider_type} with model {model_id}")
        
        try:
            if provider_type == "openrouter":
                provider = OpenRouterProvider(model_id)
            elif provider_type == "google":
                provider = GeminiProvider(model_id)
            elif provider_type == "groq":
                provider = GroqProvider(model_id)
            elif provider_type == "anthropic":
                provider = AnthropicProvider(model_id)
            elif provider_type == "cerebras":
                provider = CerebrasProvider(model_id)
            elif provider_type == "mistral":
                provider = MistralProvider(model_id)
            else:
                logger.error(f"Unknown provider type: {provider_type}")
                return None
                
            self._providers[cache_key] = provider
            return provider
            
        except Exception as e:
            logger.error(f"Failed to initialize provider {provider_type}: {e}")
            return None

    def _resolve_config(self, model_name: str = None) -> dict:
        """Map a model name to its SLM_LIST config, falling back to the
        default. Pure lookup - does NOT mutate any shared state, so it is
        safe to call from concurrent requests."""
        if model_name:
            return next(
                (item for item in SLM_LIST if item["name"] == model_name),
                self.default_model_config,
            )
        return self.default_model_config

    def load_model(self, model_name: str = None):
        """
        Warm up a provider so the first real request isn't slow (used at
        startup). This is the one place current_model_name is set, and it is
        only read by the informational "/" status endpoint - the request path
        no longer depends on it (see generate_response), so there is no
        shared-state race between concurrent /chat calls.
        """
        config = self._resolve_config(model_name)
        if model_name:
            self.current_model_name = model_name
        if config:
            self._get_provider_instance(config)

    def ensure_provider(self, model_name: str = None):
        """
        Resolve and initialize the provider for model_name, raising
        LLMProviderError if it can't be created. Lets callers fail fast -
        e.g. before spending a paid web-search call - when the selected model
        isn't usable at all (unknown provider or a missing API key). Note this
        only catches setup failures; a bad-key/quota error the provider's API
        returns at call time still surfaces later from generate_response.
        """
        config = self._resolve_config(model_name)
        if not config:
            raise LLMProviderError("No model configured.")

        provider = self._get_provider_instance(config)
        if not provider:
            raise LLMProviderError(
                f"Could not initialize provider for {config.get('name')}. "
                "Please check API keys."
            )
        return provider

    @staticmethod
    def _is_configured(config: dict) -> bool:
        """True if this provider's API key is present, so it's worth trying."""
        env = PROVIDER_ENV.get(config.get("provider"))
        return bool(env and os.environ.get(env))

    def _fallback_order(self, model_name: str = None) -> list:
        """
        Build the ordered list of models to attempt: the requested model
        first, then every OTHER configured provider (API key present) in
        SLM_LIST order as a fallback. Providers with no key are skipped so a
        free-tier rate-limit on the primary rolls to the next usable provider
        instead of failing, and we never waste a call on an unconfigured one.
        """
        primary = self._resolve_config(model_name)
        order = []
        if primary:
            order.append(primary)
        for cfg in SLM_LIST:
            if cfg is primary or cfg in order:
                continue
            if self._is_configured(cfg):
                order.append(cfg)
        return order

    def ensure_any_provider(self, model_name: str = None):
        """
        Ensure at least one provider in the fallback order can be initialized.
        Lets callers fail fast (e.g. before a paid web-search call) only when
        NO model is usable at all, rather than tripping on the primary alone.
        """
        last_error = None
        for config in self._fallback_order(model_name):
            try:
                return self.ensure_provider(config.get("name"))
            except LLMProviderError as e:
                last_error = e
        raise last_error or LLMProviderError("No model configured.")

    def generate_response_with_model(
        self,
        message: str,
        persona: str = "General Assistant",
        model_name: str = None,
        max_tokens: int = 512,
        history: list = None,
    ) -> tuple:
        """
        Generate a response, transparently falling back to other configured
        providers if the selected one fails (e.g. a free-tier 429 or a hung
        upstream). Returns (text, model_name_actually_used). Raises
        LLMProviderError only if every candidate fails.

        Model resolution is per-call (no shared self.current_model_name), so
        concurrent requests can't clobber each other's routing.
        """
        configs = self._fallback_order(model_name)
        if not configs:
            raise LLMProviderError("No model configured.")

        system_prompt = _build_system_prompt(persona)

        errors = []
        for i, config in enumerate(configs):
            name = config.get("name")
            try:
                provider = self.ensure_provider(name)
                text = provider.generate_response(system_prompt, message, max_tokens=max_tokens, history=history)
                # Backstop: if a personal-advice question got flattened to a
                # bare yes/no, append the required framing.
                note = advice_safety_note(message, text)
                if note:
                    text = f"{text.strip()}\n\n{note}"
                if i > 0:
                    logger.info(
                        f"Fallback: '{name}' answered after {i} provider(s) failed."
                    )
                return text, name
            except LLMProviderError as e:
                logger.warning(
                    f"Provider '{name}' failed ({i + 1}/{len(configs)}): {e}"
                )
                errors.append(f"{name}: {e}")

        raise LLMProviderError("All providers failed. " + " | ".join(errors))

    def stream_response_with_model(
        self,
        message: str,
        persona: str = "General Assistant",
        model_name: str = None,
        max_tokens: int = 512,
        history: list = None,
    ):
        """
        Stream a response as text chunks, with the same provider-fallback
        semantics as generate_response_with_model - but fallback is only
        possible BEFORE the first chunk is emitted (once bytes have been sent to
        the client, switching providers mid-answer isn't possible). If a
        provider fails after streaming has started, a short interruption note is
        appended and streaming stops.

        Yields str chunks. Raises LLMProviderError only if NO provider produced
        any output at all.
        """
        configs = self._fallback_order(model_name)
        if not configs:
            raise LLMProviderError("No model configured.")

        system_prompt = _build_system_prompt(persona)

        errors = []
        for i, config in enumerate(configs):
            name = config.get("name")
            started = False
            try:
                provider = self.ensure_provider(name)
                for piece in provider.stream_response(
                    system_prompt, message, max_tokens=max_tokens, history=history
                ):
                    started = True
                    yield piece
                if started:
                    if i > 0:
                        logger.info(
                            f"Fallback (stream): '{name}' answered after "
                            f"{i} provider(s) failed."
                        )
                    return
                # Provider streamed nothing - treat as a failure and try next.
                errors.append(f"{name}: empty stream")
            except LLMProviderError as e:
                if started:
                    # Already streamed partial output; can't switch providers.
                    logger.error(f"Provider '{name}' failed mid-stream: {e}")
                    yield f"\n\n_[stream interrupted: {e}]_"
                    return
                logger.warning(
                    f"Provider '{name}' failed before streaming "
                    f"({i + 1}/{len(configs)}): {e}"
                )
                errors.append(f"{name}: {e}")

        raise LLMProviderError("All providers failed (stream). " + " | ".join(errors))

    def generate_response(
        self,
        message: str,
        persona: str = "General Assistant",
        model_name: str = None,
        max_tokens: int = 512,
        history: list = None,
    ) -> str:
        """
        Generate a response (with provider fallback), returning just the text.
        Thin wrapper over generate_response_with_model for callers that don't
        need to know which provider actually answered.
        """
        text, _ = self.generate_response_with_model(
            message, persona, model_name, max_tokens=max_tokens, history=history
        )
        return text

# Singleton usage
llm_engine = LLMEngine.get_instance()
