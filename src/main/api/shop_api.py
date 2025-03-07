from flask import Blueprint, request, jsonify
import logging
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
blueprint = Blueprint('product_eval', __name__)

@blueprint.route("/api/v1/product_recommender/", methods=['GET'])
def product_recommender():
    pass