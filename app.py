import os
from flask import Flask
from dotenv import load_dotenv
from src.main.api.shop_api import blueprint

load_dotenv()  

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure app for handling async routes
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    # Register blueprints
    app.register_blueprint(blueprint)
    return app

if __name__ == "__main__":
    app = create_app()
    
    # For development with async support
    import asyncio
    from hypercorn.config import Config
    from hypercorn.asyncio import serve
    
    config = Config()
    config.bind = ["0.0.0.0:8000"]  # Bind to all interfaces on port 8000
    config.use_reloader = True
    
    # Run with Hypercorn (ASGI server with async support)
    asyncio.run(serve(app, config))
    
    # Don't use this for async routes:
    # app.run(debug=True)