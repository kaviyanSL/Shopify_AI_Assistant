import os
from flask import Flask
from flask_session import Session
from src.main.api.shop_api import blueprint
import redis
from dotenv import load_dotenv

load_dotenv()

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

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
