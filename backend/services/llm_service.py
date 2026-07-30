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

        from utils.persona_manager import get_persona_prompt
        persona_instructions = get_persona_prompt(persona)
        system_prompt = f"You are a helpful AI finance assistant. {persona_instructions}"

        errors = []
        for i, config in enumerate(configs):
            name = config.get("name")
            try:
                provider = self.ensure_provider(name)
                text = provider.generate_response(system_prompt, message)
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

    def generate_response(
        self,
        message: str,
        persona: str = "General Assistant",
        model_name: str = None,
    ) -> str:
        """
        Generate a response (with provider fallback), returning just the text.
        Thin wrapper over generate_response_with_model for callers that don't
        need to know which provider actually answered.
        """
        text, _ = self.generate_response_with_model(message, persona, model_name)
        return text

# Singleton usage
llm_engine = LLMEngine.get_instance()
