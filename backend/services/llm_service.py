import logging
from config.slm_config import SLM_LIST
from backend.services.api_providers import (
    OpenRouterProvider,
    GeminiProvider,
    GroqProvider,
    AnthropicProvider
)

logger = logging.getLogger(__name__)

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
            else:
                logger.error(f"Unknown provider type: {provider_type}")
                return None
                
            self._providers[cache_key] = provider
            return provider
            
        except Exception as e:
            logger.error(f"Failed to initialize provider {provider_type}: {e}")
            return None

    def load_model(self, model_name: str = None):
        """
        In the API context, this mostly just sets the active configuration
        and verifies the provider can be initialized.
        """
        if model_name:
            self.current_model_name = model_name
            
        if self.current_model_name:
            config = next((item for item in SLM_LIST if item["name"] == self.current_model_name), self.default_model_config)
            self._get_provider_instance(config)

    def generate_response(self, message: str, persona: str = "General Assistant") -> str:
        """
        Generates a response using the selected model via its API provider.
        """
        if not self.current_model_name:
             return "Error: No model configured."
             
        config = next((item for item in SLM_LIST if item["name"] == self.current_model_name), self.default_model_config)
        
        provider = self._get_provider_instance(config)
        if not provider:
            return f"Error: Could not initialize provider for {self.current_model_name}. Please check API keys."

        from utils.persona_manager import get_persona_prompt
        persona_instructions = get_persona_prompt(persona)
        
        system_prompt = f"You are a helpful AI finance assistant. {persona_instructions}"

        return provider.generate_response(system_prompt, message)

# Singleton usage
llm_engine = LLMEngine.get_instance()
