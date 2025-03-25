from flask import Blueprint, request, jsonify
import requests
import logging
import ast
import os
from src.main.service.ShopDataCallingService import ShopDataCallingService
from src.main.service.DeepSeekService import DeepSeekService
from src.main.common.ShopifyGraphQLClient import ShopifyGraphQLClient
from src.main.service.SemanticSearchService import SemanticSearchService
from src.main.repository.ProductRepository import ProductRepository
from src.main.service.TextPreprocessingService import TextPreprocessingService
from src.main.service.SentimentService.SentimentService import SentimentService
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
    model= DeepSeekService() 
    product_category = model.ai_response(prompt, data_class.calling_data(product_category))

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

        
        ShopDataCalling = ShopDataCallingService()
        ShopDataCalling.saving_shop_data_to_db(product)
          
        logging.info("response is compeleted")
        return jsonify({"message":"all data already fetched"}), 200


    except requests.exceptions.RequestException as e:
        logging.error("Error in API request", exc_info=True)
        return jsonify({"error": "API request failed", "details": str(e)}), 500
    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    

@blueprint.route("/api/v1/fetch_all_product_from_store_graphQL/", methods=['POST'])
def fetch_all_product_from_store_graphQL():
    try:
        
        shopify_client = ShopifyGraphQLClient()
        product = shopify_client.fetch_products()
        
        ShopDataCalling = ShopDataCallingService()
        ShopDataCalling.saving_shop_data_to_db_graphql(product)
          
        logging.info("response is compeleted")
        return jsonify({"message":"all data already fetched"}), 200


    except requests.exceptions.RequestException as e:
        logging.error("Error in API request", exc_info=True)
        return jsonify({"error": "API request failed", "details": str(e)}), 500
    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    
@blueprint.route("/api/v1/search_results_recommender_using_semantic/", methods=['GET'])
def search_results_recommender_using_semantic():
    try:
        request_api = request.get_json()
        prompt = request_api.get('prompt')
        text_preprocessor = TextPreprocessingService()
        prompt = text_preprocessor.prompt_spell_correction(prompt)
        semantinc_model = SemanticSearchService()
        distance,index = semantinc_model.semantic_search_result(prompt)
        logging.info("semantic_search_result is compeleted")
        repo = ProductRepository()
        product_variant_ids = repo.product_variant_ids_call(index)
        logging.info("product_variant_ids_call is compeleted")
        product_ids = [j[0] for j in [ast.literal_eval(i[1]) for i in product_variant_ids]]
        variants_ids = [j[1] for j in [ast.literal_eval(i[1]) for i in product_variant_ids]]
        prosuct_data = repo.call_products(product_ids)
        variant_data = repo.call_variants(variants_ids)
        logging.info("call_products and call_variants is compeleted")

        deep_seek_model = DeepSeekService()
        ai_response = deep_seek_model.deep_seek_response_V2(prompt,prosuct_data,variant_data)
        del deep_seek_model
          
        logging.info("response is compeleted")
        return jsonify({"message":f"{ai_response}"}), 200


    except requests.exceptions.RequestException as e:
        logging.error("Error in API request", exc_info=True)
        return jsonify({"error": "API request failed", "details": str(e)}), 500
    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    

@blueprint.route("/api/v1/test/", methods=['GET'])
def test():
    try:
        list_of_commments =  [
                            "very good product",
                            "very bad product",
                            "not sure if it is a good or bad product"
                            ]
        model = SentimentService()
        results = model.sentiment_analaysis(list_of_commments)
        del model
        logging.info("response is compeleted")
        return jsonify({"message":results}), 200


    except requests.exceptions.RequestException as e:
        logging.error("Error in API request", exc_info=True)
        return jsonify({"error": "API request failed", "details": str(e)}), 500
    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500