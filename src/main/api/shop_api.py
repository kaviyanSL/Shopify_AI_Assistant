from flask import Blueprint, request, jsonify, session
import requests
import logging
import ast
import shutil
import os
from src.main.service.ShopDataCallingService import ShopDataCallingService
from src.main.service.DeepSeekService import DeepSeekService
from src.main.common.ShopifyGraphQLClient import ShopifyGraphQLClient
from src.main.service.SemanticSearchService import SemanticSearchService
from src.main.repository.ProductRepository import ProductRepository
from src.main.service.TextPreprocessingService import TextPreprocessingService
from src.main.service.SentimentService.SentimentService import SentimentService
from src.main.service.agent_service.AgentAIService import AgentAIService
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
    

@blueprint.route("/api/v1/search_results_recommender_using_semantic_deepseek_api/", methods=['POST'])
def search_results_recommender_using_semantic_deepseek_api():
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
        ai_response = deep_seek_model.deep_seek_response_api(prompt,prosuct_data,variant_data)
        del deep_seek_model
          
        logging.info("response is compeleted")
        return jsonify({"message":f"{ai_response}"}), 200


    except requests.exceptions.RequestException as e:
        logging.error("Error in API request", exc_info=True)
        return jsonify({"error": "API request failed", "details": str(e)}), 500
    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    

@blueprint.route("/api/v1/creating_semantic_model_based_on_peyman_datamodel/", methods=['GET'])
def creating_semantic_model_based_on_peyman_datamodel():
    try:
        ShopDataCalling = ShopDataCallingService()
        ShopDataCalling.saving_product_variants_is_using_peyman_db()


    except requests.exceptions.RequestException as e:
        logging.error("Error in API request", exc_info=True)
        return jsonify({"error": "API request failed", "details": str(e)}), 500
    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    
       

@blueprint.route("/api/v1/search_results_recommender_using_semantic_peyman_db_deepseek_api/", methods=['POST'])
def search_results_recommender_using_semantic_peyman_db_deepseek_api():
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
        prosuct_data = repo.call_products_peyman_data_model(product_ids)
        variant_data = repo.call_variants_peyman_data_model(variants_ids)
        logging.info("call_products and call_variants is compeleted")

        deep_seek_model = DeepSeekService()
        ai_response = deep_seek_model.deep_seek_response_api_peyman_db(prompt,prosuct_data,variant_data)
        del deep_seek_model
          
        logging.info("response is compeleted")
        return jsonify({"message":f"{ai_response}"}), 200


    except requests.exceptions.RequestException as e:
        logging.error("Error in API request", exc_info=True)
        return jsonify({"error": "API request failed", "details": str(e)}), 500
    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    

@blueprint.route("/api/v1/search_results_recommender_using_semantic_peyman_db_qwen2.5/", methods=['POST'])
def search_results_recommender_using_semantic_peyman_db_qwen2():
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
        prosuct_data = repo.call_products_peyman_data_model(product_ids)
        variant_data = repo.call_variants_peyman_data_model(variants_ids)
        logging.info("call_products and call_variants is compeleted")

        agent = DeepSeekService()
        ai_response = agent.qwen2_5_response(prompt,prosuct_data,variant_data)
        del agent
          
        logging.info("response is compeleted")
        return jsonify({"message":f"{ai_response}"}), 200


    except requests.exceptions.RequestException as e:
        logging.error("Error in API request", exc_info=True)
        return jsonify({"error": "API request failed", "details": str(e)}), 500
    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    

@blueprint.route("/api/v1/agent_qwen_chat/", methods=['POST'])
def agent_qwen_chat():
    try:
        agent = AgentAIService()
        user_input = request.json.get('query')

        if not user_input:
            return jsonify({"error": "No query provided"}), 400

        # Ensure session dictionary exists
        if 'filters' not in session:
            session['filters'] = {}

        # Extract new filters
        filters = agent.extract_query_filters(user_input)

        # Debug: Print session before update
        logging.info(f"Session before update: {session['filters']}")

        # Merge new filters with old filters (avoids overwriting)
        for key, value in filters.items():
            if value:  # Only update non-null values
                session['filters'][key] = value

        session.modified = True  # Ensure Flask saves changes

        # Debug: Print session after update
        logging.info(f"Session after update: {session['filters']}")

        # Check what is missing
        missing_fields = []
        if not session['filters'].get('product_type'):
            missing_fields.append("product category")
        if not session['filters'].get('price'):
            missing_fields.append("max price")

        if missing_fields:
            return jsonify({"message": f"I still need more details. Could you provide {', '.join(missing_fields)}?"})

        # Retrieve filters
        status = session['filters'].get("status")
        product_type = session['filters'].get("product_type")
        max_price = session['filters'].get("price")

        # Query the database
        repo = ProductRepository()
        products = repo.call_products(status, product_type, max_price)

        if products:
            result = [{"title": p.title, "status": p.status, "product_type": p.product_type, "price": p.price} for p in products]
            return jsonify({"message": result}), 200
        else:
            return jsonify({"message": "No products found matching your criteria."})

    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500



@blueprint.route("/api/v1/agent_qwen_continue_chat/", methods=['POST'])
def agent_qwen_continue_chat():
    try:
        agent = AgentAIService()
        user_input = request.json.get('query')

        if not user_input:
            return jsonify({"error": "No query provided"}), 400

        # Ensure session exists
        if 'filters' not in session:
            session['filters'] = {}

        # Extract filters and update session
        filters = agent.extract_query_filters(user_input)

        # Debug: Print session before update
        logging.info(f"Session before update: {session['filters']}")

        # Merge values instead of overwriting
        for key, value in filters.items():
            if value:
                # Convert price to string if it's an integer
                if key == "price" and isinstance(value, int):
                    value = str(value)
                session['filters'][key] = value

        session.modified = True  # Persist session updates

        # Debug: Print session after update
        logging.info(f"Session after update: {session['filters']}")

        # Check for missing fields
        missing_fields = []
        if not session['filters'].get('product_type'):
            missing_fields.append("product category")
        if not session['filters'].get('price'):
            missing_fields.append("max price")

        if missing_fields:
            return jsonify({"message": f"I still need more details. Could you provide {', '.join(missing_fields)}?"})

        # Retrieve stored filters
        status = session['filters'].get("status")
        product_type = session['filters'].get("product_type")
        max_price = session['filters'].get("price")

        # Convert max_price to a float for comparison
        try:
            max_price = float(max_price)
        except ValueError:
            return jsonify({"error": "Invalid price format provided."}), 400

        # Calculate price range (±25%)
        min_price = max_price * 0.75
        max_price = max_price * 1.25

        # Query the database again
        repo = ProductRepository()
        products = repo.call_products(status, product_type, max_price)

        # Filter products within the price range
        filtered_products = [
            {"title": p.title, "status": p.status, "product_type": p.product_type, "price": p.price}
            for p in products if min_price <= p.price <= max_price
        ]

        if filtered_products:
            response = jsonify({"message": filtered_products}), 200
        else:
            response = jsonify({"message": "No products found matching your criteria."}), 200

        # Clear the flask_session directory
        flask_session_path = os.path.join(os.getcwd(), 'flask_session')
        if os.path.exists(flask_session_path):
            shutil.rmtree(flask_session_path)
            logging.info("Flask session directory cleared.")

        return response

    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500