import os
import logging

logger = logging.getLogger(__name__)

class BaseLLMProvider:
    """Base class for all LLM providers."""
    def __init__(self, model_id: str):
        self.model_id = model_id

    def generate_response(self, system_prompt: str, user_message: str) -> str:
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
        user_message: str
    ) -> str:

        try:

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                temperature=0.7,
                max_tokens=512
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

            return (
                f"OpenRouter Error: {str(e)}"
            )

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

    def generate_response(self, system_prompt: str, user_message: str) -> str:
        try:
            combined_prompt = f"""
            System Instructions:
            {system_prompt}

            User Message:
            {user_message}
            """

            response = self.model.generate_content(combined_prompt)

            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return f"Gemini Error: {str(e)}"


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

    def generate_response(self, system_prompt: str, user_message: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=512,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Groq API Error: {e}")
            return f"Error gathering insights from Groq: {str(e)}"


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

    def generate_response(self, system_prompt: str, user_message: str) -> str:
        try:
            response = self.client.messages.create(
                model=self.model_id,
                system=system_prompt,
                max_tokens=512,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Anthropic API Error: {e}")
            return f"Error gathering insights from Anthropic: {str(e)}"


# =========================================================
# Local TinyLlama Provider
# =========================================================
class LocalProvider(BaseLLMProvider):
    def __init__(self, model_id: str):
        super().__init__(model_id)

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(
            f"Initializing Local Provider: {self.model_id} on {self.device}"
        )

        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)

            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )

            self._pipe = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
                device=-1 if self.device == "cpu" else 0,
                max_new_tokens=256,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.95
            )

        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            self._pipe = None

    def generate_response(self, system_prompt: str, user_message: str) -> str:

        if not self._pipe:
            return "Error: Local model failed to load. Please check logs."

        prompt = (
            f"<|system|>\n"
            f"{system_prompt}\n"
            f"</s>\n"
            f"<|user|>\n"
            f"{user_message}\n"
            f"</s>\n"
            f"<|assistant|>\n"
        )

        try:
            outputs = self._pipe(prompt)

            generated_text = outputs[0]['generated_text']

            response = generated_text.split(
                "<|assistant|>\n"
            )[-1].strip()

            return response

        except Exception as e:
            logger.error(f"Local Generation failed: {e}")
            return f"Error gathering insights: {str(e)}"