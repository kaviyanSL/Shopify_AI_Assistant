from flask import Blueprint, request, jsonify
import logging
import asyncio
from src.main.service.agent_service.Groq_Agent import agent_calling
from src.main.service.agent_service.Groq_Agent_Query import agent_calling_query
from src.main.service.agent_service.Groq_Agent_Service import agent_calling_service
from dotenv import load_dotenv

load_dotenv()  

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Initializing Shopify agent API blueprint")
blueprint = Blueprint('product_eval', __name__)

# Helper to run async functions in sync context
def run_async(async_func, *args, **kwargs):
    return asyncio.run(async_func(*args, **kwargs))

@blueprint.route("/api/v1/Grog_Agent_test", methods=["POST"])
def Grog_Agent_test():
    logger.info("Received request to /api/v1/Grog_Agent endpoint")
    try:
        data = request.get_json()
        logger.debug(f"Request data: {data}")
        
        user_prompt = data.get("query", "")
        session_id = data.get("session_id", None)
        if not user_prompt:
            logger.warning("Request missing required 'query' field")
            return jsonify({"error": "Missing query"}), 400
        
        logger.info(f"Processing agent request with prompt: {user_prompt[:50]}...")
        response = run_async(agent_calling, user_prompt, session_id)
        logger.info("Successfully processed agent request")
        logger.debug(f"Response generated: {str(response)[:200]}...")
        
        return jsonify({"response": response})

    except Exception as e:
        logger.error(f"Error in Grog_Agent endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@blueprint.route("/api/v1/Grog_Agent_Query", methods=["POST"])
def Grog_Agent_Query():
    logger.info("Received request to /api/v1/Grog_Agent_Query endpoint")
    try:
        data = request.get_json()
        logger.debug(f"Request data: {data}")
        
        user_prompt = data.get("query", "")
        if not user_prompt:
            logger.warning("Request missing required 'query' field")
            return jsonify({"error": "Missing query"}), 400

        logger.info(f"Processing query agent request with prompt: {user_prompt[:50]}...")
        response = run_async(agent_calling_query, user_prompt)
        logger.info("Successfully processed query agent request")
        logger.debug(f"Response generated: {str(response)[:200]}...")
        
        return jsonify({"response": response})

    except Exception as e:
        logger.error(f"Error in Grog_Agent_Query endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@blueprint.route("/api/v1/Grog_Agent", methods=["POST"])
def Grog_Agent():
    logger.info("Received request to /api/v1/Grog_Agent endpoint")
    try:
        data = request.get_json()
        logger.debug(f"Request data: {data}")
        
        user_prompt = data.get("query", "")
        session_id = data.get("session_id", None)
        if not user_prompt:
            logger.warning("Request missing required 'query' field")
            return jsonify({"error": "Missing query"}), 400
        
        logger.info(f"Processing agent request with prompt: {user_prompt[:50]}...")
        response = run_async(agent_calling_service, user_prompt, session_id)
        logger.info("Successfully processed agent request")
        logger.debug(f"Response generated: {str(response)[:200]}...")
        
        return jsonify({"response": response})

    except Exception as e:
        logger.error(f"Error in Grog_Agent endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500