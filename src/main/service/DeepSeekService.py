from src.main.service.GarbageCollectorServicec import GarbageCollectorServicec
import requests
import json
import os
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
from dotenv import load_dotenv

load_dotenv()


class DeepSeekService:
    def __init__ (self):
        pass
    def ai_response(self,prompt,datasets):
        url = os.getenv("DEEPSEEK_URL_LOCAL")

        datasets_json = json.dumps(datasets)

        data = {
                "model": "deepseek-r1:14B",
                "prompt": f"""
                Customer Request: {prompt}  
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
        

    def deep_seek_response_V2(self, prompt, products, variants):
        url = os.getenv("DEEPSEEK_URL_LOCAL")

        product_descriptions = [
            f"product id : {product[0]}"
            f"name:{product[1]} - category: {product[-1]}, color {(variant[2])},price ${variant[3]}, "
            f"inventory_quantity:{variant[4]},status {product[6]},gender: {(product[5])}"
            for product, variant in zip(products, variants)
        ]

        data = {
            "model": "deepseek-r1:14B",
            "prompt": f"""
            Customer Request: {prompt}  
            Products: {product_descriptions}  

            Task:  
            - Identify and recommend products from the product descriptions that match the customer's request based on product details (e.g., color, category), ignoring case sensitivity.

            - If an exact match is found, but the inventory_quantity is 0, respond with:
            "The product you are looking for is currently out of stock, but here are the next best matching products."

            - If no exact match exists, suggest the best available alternatives within the same category and color or closest possible matches, ensuring that the alternatives are in stock and active.

            - If no suitable products are found, respond with:
            "The product you are looking for is not listed as one of our current products."

            - Do not suggest products that are archived or have a status other than "active."

            - Output only the final response in a short, concise format, followed by the matching products in JSON format.

            - Ensure the response uses the same language as the original customer prompt, and if necessary, handle translation or tone adjustment to fit the user's style.

            - If there are multiple possible matches or alternatives, list the most relevant ones based on the color and availability.
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
        



    def deep_seek_response_api(self, prompt, products, variants):
        url = os.getenv("DEEPSEEK_API_URL")
        api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not url or not api_key:
            raise ValueError("Missing DeepSeek API URL or API Key in environment variables")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Create product descriptions
        product_descriptions = [
            f"product id: {product[0]}, "
            f"name: {product[1]} - category: {product[-1]}, color: {variant[2]}, price: ${variant[3]}, "
            f"inventory_quantity: {variant[4]}, status: {product[6]}, gender: {product[5]}"
            for product, variant in zip(products, variants)
        ]

        # Construct the messages in proper chat format
        messages = [
            {
                "role": "system",
                "content": """You are a helpful shopping assistant. Your task is to help customers find products."""
            },
            {
                "role": "user",
                "content": f"""
                Customer Request: {prompt}  
                Products: {product_descriptions}  

                Task:  
                - Identify and recommend products from the product descriptions that match the customer's request based on product details (e.g., color, category), ignoring case sensitivity.

                - If an exact match is found, but the inventory_quantity is 0, respond with:
                "The product you are looking for is currently out of stock, but here are the next best matching products."

                - If no exact match exists, suggest the best available alternatives within the same category and color or closest possible matches, ensuring that the alternatives are in stock and active.

                - If no suitable products are found, respond with:
                "The product you are looking for is not listed as one of our current products."

                - Do not suggest products that are archived or have a status other than "active."

                - Output only the final response in a short, concise format, followed by the matching products in JSON format.

                - Ensure the response uses the same language as the original customer prompt, and if necessary, handle translation or tone adjustment to fit the user's style.

                - If there are multiple possible matches or alternatives, list the most relevant ones based on the color and availability.
                """
            }
        ]

        payload = {
            "model": "deepseek-chat",  # Specify the model you want to use
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.3  # Lower temperature for more factual responses
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # Raises exception for 4XX/5XX errors
            
            # Parse the response
            response_data = response.json()
            
            # Extract the assistant's reply
            if "choices" in response_data and len(response_data["choices"]) > 0:
                assistant_reply = response_data["choices"][0]["message"]["content"]
                return assistant_reply
            else:
                return "Received unexpected response format from DeepSeek API"

        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            return f"Error communicating with DeepSeek API: {str(e)}"
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse API response: {e}")
            return "Error processing DeepSeek API response"
        

    def deep_seek_response_api_peyman_db(self, prompt, products, variants):
        url = os.getenv("DEEPSEEK_API_URL")
        api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not url or not api_key:
            raise ValueError("Missing DeepSeek API URL or API Key in environment variables")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        #TODO : remmeber to add column(products[tag] = gender, variants[color] = color),
        product_descriptions = [
            f"product id: {product[1]}, "
            f"name: {product[3]} - category: {product[6]}, price: ${variant[4]}, "
            f"inventory_quantity: {variant[6]}, status: {product[8]}"
            for product, variant in zip(products, variants)
        ]

        # Construct the messages in proper chat format
        messages = [
            {
                "role": "system",
                "content": """You are a helpful shopping assistant. Your task is to help customers find products."""
            },
            {
                "role": "user",
                "content": f"""
                Customer Request: {prompt}  
                Products: {product_descriptions}  

                Task:  
                - Identify and recommend products from the product descriptions that match the customer's request based on product details (e.g., color, category), ignoring case sensitivity.

                - If an exact match is found, but the inventory_quantity is 0, respond with:
                "The product you are looking for is currently out of stock, but here are the next best matching products."

                - If no exact match exists, suggest the best available alternatives within the same category and color or closest possible matches, ensuring that the alternatives are in stock and active.

                - If no suitable products are found, respond with:
                "The product you are looking for is not listed as one of our current products."

                - Do not suggest products that are archived or have a status other than "active."

                - Output only the final response in a short, concise format, followed by the matching products in JSON format.

                - Ensure the response uses the same language as the original customer prompt, and if necessary, handle translation or tone adjustment to fit the user's style.

                - If there are multiple possible matches or alternatives, list the most relevant ones based on the color and availability.
                """
            }
        ]

        payload = {
            "model": "deepseek-chat",  # Specify the model you want to use
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.3  # Lower temperature for more factual responses
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # Raises exception for 4XX/5XX errors
            
            # Parse the response
            response_data = response.json()
            
            # Extract the assistant's reply
            if "choices" in response_data and len(response_data["choices"]) > 0:
                assistant_reply = response_data["choices"][0]["message"]["content"]
                return assistant_reply
            else:
                return "Received unexpected response format from DeepSeek API"

        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            return f"Error communicating with DeepSeek API: {str(e)}"
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse API response: {e}")
            return "Error processing DeepSeek API response"
        



    def qwen2_5_response(self, prompt, products, variants):
        url = os.getenv("QWEN_API_URL")  # Update this with your actual API URL

        product_descriptions = [
            f"product id: {product[0]}, "
            f"name: {product[1]} - category: {product[-1]}, color: {variant[2]}, price: ${variant[3]}, "
            f"inventory_quantity: {variant[4]}, status: {product[6]}, gender: {product[5]}"
            for product, variant in zip(products, variants)
        ]

        messages = [
            {"role": "system", "content": "You are an AI assistant helping with product recommendations."},
            {"role": "user", "content": f"""
            Customer Request: {prompt}  
            Products: {product_descriptions}  

            Task:  
            - Identify and recommend products from the product descriptions that match the customer's request based on product details (e.g., color, category), ignoring case sensitivity.
            - If an exact match is found, but the inventory_quantity is 0, respond with:
            "The product you are looking for is currently out of stock, but here are the next best matching products."
            - If no exact match exists, suggest the best available alternatives within the same category and color or closest possible matches, ensuring that the alternatives are in stock and active.
            - If no suitable products are found, respond with:
            "The product you are looking for is not listed as one of our current products."
            - Do not suggest products that are archived or have a status other than 'active.'
            - Output only the final response in a short, concise format, followed by the matching products in JSON format.
            - Ensure the response uses the same language as the original customer prompt.
            - If there are multiple possible matches or alternatives, list the most relevant ones based on the color and availability.
            """}
        ]

        data = {
            "model": "qwen2.5-coder",
            "messages": messages,
            "stream": True  # If streaming is supported, otherwise remove
        }

        response = requests.post(url, json=data, stream=True)

        if response.status_code == 200:
            final_answer = ""

            try:
                for line in response.iter_lines():
                    if line:
                        try:
                            response_data = json.loads(line.decode('utf-8'))

                            if "content" in response_data:
                                final_answer += response_data["content"]

                        except json.JSONDecodeError as e:
                            logging.debug(f"Error decoding JSON: {e}")

            finally:
                response.close()  # Ensure the response stream is closed

            return final_answer.strip()

        else:
            return f"Request failed with status code: {response.status_code}"

        

    def __del__(self):
        logging.debug("DeepSeekService object deleted")





