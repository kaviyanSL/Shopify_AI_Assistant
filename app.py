import os
from flask import Flask
from flask_session import Session
from src.main.api.shop_api import blueprint

def create_app():
    app = Flask(__name__)
    
    # Secret key for session encryption (Ensure this is set in your environment)
    app.secret_key = os.getenv("CHATBOT_SECRET_KEY", "fallback_secret_key")

    # Configure Flask-Session to use filesystem-based session storage
    app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions on the server
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_FILE_DIR'] = './flask_session/'  # Ensure this directory exists
    
    Session(app)  # Initialize Flask-Session
    
    # Register your API blueprint
    app.register_blueprint(blueprint)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
