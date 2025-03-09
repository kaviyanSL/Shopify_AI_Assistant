from src.main.service.GarbageCollectorServicec import GarbageCollectorServicec
import requests
import json
import os
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
from dotenv import load_dotenv

load_dotenv()


class DeepSeekService:
    def __init__ (self,prompt,datasets):
        self.prompt = prompt
        self.datasets = datasets
    def ai_response(self):
        url = os.getenv("DEEPSEEK_URL_LOCAL")

        datasets_json = json.dumps(self.datasets)

        data = {
                "model": "deepseek-r1:14B",
                "prompt": f"""
                Customer Request: {self.prompt}  
                Dataset JSON: {datasets_json}  

                Task:  
                - Identify and recommend products from the dataset that match the customer's request.  
                - If no exact match exists, suggest the best alternatives within the same category.  
                - If no suitable product is found, respond with:  
                "The product you are looking for is not listed as one of our current products."  
                - Do **not** include any JSON response if no product matches.  
                - Output **only** the final response in a short, concise format, followed by matching products in JSON format.  
                - Maintain the same language as the prompt (translate if necessary).  
                """,
            }



        response = requests.post(url, json=data, stream=True)

        if response.status_code == 200:
            final_answer = ""

            try:
                for line in response.iter_lines():
                    if line:
                        try:
                            response_data = json.loads(line.decode('utf-8'))

                            if "response" in response_data:
                                final_answer += response_data["response"]

                            if response_data.get("done", False):
                                break
                        except json.JSONDecodeError as e:
                            logging.debug(f"Error decoding JSON: {e}")

            finally:
                gc = GarbageCollectorServicec(response)
                gc.garbage_collecting()

            return final_answer.replace("<think>", "").replace("</think>", "")

        else:
            return f"Request failed with status code: {response.status_code}"


