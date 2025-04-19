import os
from flask import Flask, request, jsonify, session
from flask_session import Session
from dotenv import load_dotenv
import redis
from src.main.api.shop_api import blueprint

load_dotenv()  

def create_app():
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)