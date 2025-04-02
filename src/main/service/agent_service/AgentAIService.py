import ollama
import logging
import json
from src.main.repository.ProductRepository import ProductRepository

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


class AgentAIService:
    def __init__(self):
        self.db = ProductRepository()

    def extract_query_filters(self, user_prompt):
        """Use Ollama to extract product status, type, and budget from user input."""
        list_of_product_type = [i[0] for i in self.db.call_distinct_product_type()]
        response = ollama.chat(
            model="qwen2.5-coder",
            messages=[{
                "role": "system",
                "content": f"Extract search filters from user queries. "
                        f"Return a JSON object with 'status' (e.g., active, archived), "
                        f"'product_type' {list_of_product_type}, "
                        f"'price' (budget). If no category is mentioned, return null.",
            }, {
                "role": "user",
                "content": user_prompt,
            }],
        )

        try:
            content = response["message"]["content"]
            clean_json = content.split('```json')[1].split('```')[0].strip()
            return json.loads(clean_json)
        except json.JSONDecodeError:
            return {}