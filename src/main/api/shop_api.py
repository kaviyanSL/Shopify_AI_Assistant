from flask import Blueprint, request, jsonify
import requests
import logging
import os
from src.main.service.ShopDataCallingService import ShopDataCallingService
from src.main.service.DeepSeekService import DeepSeekService
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
blueprint = Blueprint('product_eval', __name__)

@blueprint.route("/api/v1/product_recommender/", methods=['POST'])
def product_recommender():
    request_api = request.get_json()
    prompt = request_api.get('prompt')
    product_category = request_api.get('category')
    data_class = ShopDataCallingService()
    model= DeepSeekService(prompt, data_class.calling_data(product_category)) 
    product_category = model.ai_response()

    try:
        logging.info("response is compeleted")
        return jsonify({"response": product_category}), 200


    except Exception as e:
        logging.error("Error during reading message", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
@blueprint.route("/api/v1/fetch_all_product_from_store/", methods=['POST'])
def fetch_all_product_from_store():
    try:
        url = os.getenv("SHOP_PRODUCTS_URL")
        access_token = os.getenv("SHOP_TOKEN")
        headers = {
                    "X-Shopify-Access-Token": access_token
                }
        product = requests.get(url, headers=headers)

        if product.status_code == 200:
            ShopDataCalling = ShopDataCallingService()
            ShopDataCalling.saving_shop_data_to_db(product)
        else:
            print(f"Error: {product.status_code}, {product.text}")  

        logging.info("response is compeleted")
        return jsonify({"all data already fetched"}), 200


    except Exception as e:
        logging.error("Error during reading message", exc_info=True)
        return jsonify({"error": str(e)}), 500