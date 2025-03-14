from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import Tuple, List, Dict
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class SemanticSearchService:
    def __init__(self):
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    def embeded_product(self, product_list: Tuple[List[Dict], List[Dict]]):
        products, variants = product_list

        filtered_products = []
        filtered_variants = []
        product_ids = set(product['id'] for product in products)
        for variant in variants:
            if variant['product_id'] in product_ids:
                filtered_variants.append(variant)
                filtered_products.append(next(product for product in products if product['id'] == variant['product_id']))

        assert len(filtered_products) == len(filtered_variants), "Filtered Products and Variants lists must have the same length"

        product_descriptions = [
            f"{product['title']} - {product['type']}, {', '.join(variant['options'])}, ${variant['price']}, "
            f"{variant['inventory_quantity']}, {product['status']}, {', '.join(product['tags'] if product['tags'] else [])}"
            for product, variant in zip(filtered_products, filtered_variants)
        ]

        product_embeddings = np.array(self.model.encode(product_descriptions))
        logging.info('encode is done')
        index = faiss.IndexFlatL2(product_embeddings.shape[1])
        logging.info('IndexFlatL2 is done') 
        index.add(product_embeddings)

        product_variant_ids = list(enumerate((product['id'], variant['id']) for product, variant in zip(filtered_products, filtered_variants)))

        index_binary = faiss.serialize_index(index)
        return index_binary, product_variant_ids