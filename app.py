import os
from flask import Flask, request, jsonify, session
from flask_session import Session
from dotenv import load_dotenv
import redis
from src.main.api.shop_api import blueprint
from src.main.repository.ProductRepository import ProductRepository

load_dotenv()  # Load environment variables from .env

def create_app():
    app = Flask(__name__)
    
    # Secret key for session encryption (Ensure this is set in your environment)
    app.secret_key = os.getenv("CHATBOT_SECRET_KEY", "fallback_secret_key")

    # Configure Redis for session storage
    redis_client = redis.StrictRedis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0))
    )
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'shopify_ai_'
    app.config['SESSION_REDIS'] = redis_client

    Session(app)  # Initialize Flask-Session
    
    # Register your API blueprint
    app.register_blueprint(blueprint)

    # Define the agent_qwen_chat route
    @app.route('/api/v1/agent_qwen_chat/', methods=['POST'])
    def agent_qwen_chat():
        query = request.json.get("query")
        
        # Check if session_id exists, otherwise create a new one
        if 'session_id' not in session:
            session['session_id'] = "unique-session-id"  # Generate a unique session ID
            return jsonify({
                "message": "I still need more details. Could you provide product category, max price?",
                "session_id": session['session_id']  # Include session_id in the response
            }), 200
        else:
            # Handle subsequent queries
            return jsonify({
                "message": f"Processing your query: {query}",
                "session_id": session['session_id']  # Return the existing session_id
            }), 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)