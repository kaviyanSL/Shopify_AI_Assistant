from flask import Blueprint, request, jsonify
import logging
import os
from src.main.service.DeepSeekService import DeepSeekService
from src.main.service.ShopDataCallingService import ShopDataCallingService

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
blueprint = Blueprint('product_eval', __name__)

@blueprint.route("/api/v1/product_recommender/", methods=['POST'])
def product_recommender():
    model= DeepSeekService()
    data_class = ShopDataCallingService()
    

    request_api = request.get_json()
    prompt = request_api.get('prompt')
    product_category = prompt.get('category')
    product_category = model.ai_response(prompt,data_class.calling_data(product_category))

    try:
        return jsonify({"response": product_category}), 200


    except Exception as e:
        logging.error("Error during reading message", exc_info=True)
        return jsonify({"error": str(e)}), 500
    