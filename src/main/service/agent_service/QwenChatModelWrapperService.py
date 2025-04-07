from langchain_core.language_models import BaseLLM
from langchain_core.outputs import Generation, LLMResult
from typing import List, Optional
import ollama

class QwenChatModel(BaseLLM):
    model_name: str = "qwen2.5-coder"

    def _llm_type(self) -> str:
        return "qwen-ollama"

    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None) -> LLMResult:
        generations = []

        for prompt in prompts:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You're a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ]
            )

            content = response["message"]["content"]
            generations.append([Generation(text=content)])

        return LLMResult(generations=generations)
