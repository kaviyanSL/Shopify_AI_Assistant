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
        "prompt": f"This is my customer request: {self.prompt}. And this is the list of my dataset JSON: {datasets_json}. " +
                """You have to make a response about what product is suitable for my customer based on my dataset. 
                Remember that the product must be in my dataset's category of products. If the product that the 
                customer is looking for does not match with my shop's products, respond with:
                "The product you are looking for is not listed as one of our current products."
                and donot show any json response from our current products.
                If a matching product is found, return the final response and then provide allproducts and the theirs details in JSON format.
                Do not include any reasoning, explanations, or unnecessary details. 
                ONLY return the final response in short, concise language and the corresponding product details if a match is found
                and remmeber that if your response must be in the same language as promt language.
                remmeber that show the product that match as many as our product if there are any matches.
                """
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


