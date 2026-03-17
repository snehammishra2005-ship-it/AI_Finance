
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import logging
import os

logger = logging.getLogger(__name__)

class LLMEngine:
    """
    Handles loading and inference of Small Language Models (SLMs).
    Optimized for CPU usage if CUDA is unavailable.
    """
    
    _instance = None
    _model = None
    _tokenizer = None
    _pipe = None
    
    # Default model: TinyLlama (1.1B params) - Good balance for local CPU
    DEFAULT_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LLMEngine()
        return cls._instance

    def __init__(self):
        self.model_name = self.DEFAULT_MODEL
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initialized LLMEngine on device: {self.device}")

    def load_model(self, model_name: str = None):
        """
        Loads the model into memory. This is heavy and should be done once.
        """
        if model_name:
            self.model_name = model_name

        if self._pipe is not None:
             # Check if we need to reload (e.g. different model)
             # For now, simplistic check
             return
            
        logger.info(f"Loading model: {self.model_name}...")
        
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32, # float32 for CPU stability
                low_cpu_mem_usage=True
            )
            
            self._pipe = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
                device=-1 if self.device == "cpu" else 0, # -1 for CPU
                max_new_tokens=256,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.95
            )
            logger.info("Model loaded successfully.")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise e

    def generate_response(self, message: str, persona: str = "General Assistant") -> str:
        """
        Generates a response using the loaded model.
        """
        if self._pipe is None:
            self.load_model()

        from utils.persona_manager import get_persona_prompt
        persona_instructions = get_persona_prompt(persona)

        # Simple prompt engineering for TinyLlama Chat
        # <|system|>
        # You are a helpful AI assistant. {persona_instructions}</s>
        # <|user|>
        # {message}</s>
        # <|assistant|>
        
        prompt = (
            f"<|system|>\n"
            f"You are a helpful AI assistant. {persona_instructions}\n"
            f"</s>\n"
            f"<|user|>\n"
            f"{message}\n"
            f"</s>\n"
            f"<|assistant|>\n"
        )
        
        try:
            outputs = self._pipe(prompt)
            generated_text = outputs[0]['generated_text']
            
            # Extract only the assistant's part
            response = generated_text.split("<|assistant|>\n")[-1].strip()
            return response
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Error gathering insights: {str(e)}"

# Singleton usage
llm_engine = LLMEngine.get_instance()
