import requests
import os
import re
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import logging
from src.main.repository.ProductRepository import ProductRepository
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
from src.main.service.SemanticSearchService import SemanticSearchService


load_dotenv()

class ShopDataCallingService:
    def __init__(self):
        self.ProductRepository = ProductRepository()
        self.SemanticSearchService = SemanticSearchService()
    
    def calling_data(self,product_category):
        try:
            shop_url = os.getenv("SHOP_PRODUCTS_URL")
            access_token = os.getenv("SHOP_TOKEN")  

            headers = {
                "X-Shopify-Access-Token": access_token
            }
            product = requests.get(shop_url, headers=headers)
        except Exception as e:
            logging.debug(f"error has reised : {e}")


 
        rows = []
        for product in product.json()["products"]:
            for variant in product["variants"]:
                rows.append({
                    "Product ID": product["id"],
                    "Product Name": product["title"],
                    "Product Type": product["product_type"],
                    "Variant ID": variant["id"],
                    "Variant Option": variant["option1"],
                    "Price": float(variant["price"]),
                    "Compare at Price": float(variant["compare_at_price"]) if variant["compare_at_price"] else None,
                    "Inventory Quantity": variant["inventory_quantity"]
                })

        df = pd.DataFrame(rows)

        df_grouped = df.groupby("Product Type")

        return df_grouped.get_group(f"{product_category}").to_dict()
    
    def saving_shop_data_to_db(self, product_json):
        data = product_json
        product_data_list = []  
        variant_data_list = []  

        for product in data.json()['products']:
            product_data = {
                'id': product['id'],
                'title': product['title'],
                'description': product['body_html'],
                'vendor': product['vendor'],
                'handle': product['handle'],
                'tags': product['tags'],
                'status': product['status'],
                'created_at': product['created_at'],
                'updated_at': product['updated_at'],
                'image_url': product['image']['src'] ,
                'type': product['product_type']
            }
            
            product_data_list.append(product_data)
            
            for variant in product['variants']:
                variant_data = {
                    'id': variant['id'],
                    'product_id': product['id'],  
                    'title': variant['title'],
                    'price': float(variant['price']),  
                    'inventory_quantity': variant['inventory_quantity'],
                    'sku': variant['sku'],
                    'created_at': variant['created_at'],
                    'updated_at': variant['updated_at'],
                    'options':variant['option1'] 
                }
                
                
                variant_data_list.append(variant_data)

        semattinc_search_model,product_variant_ids = self.SemanticSearchService.embeded_product((
                                                            product_data_list,variant_data_list))
        
        self.ProductRepository.saving_semantic_searching_model(semattinc_search_model)

        self.ProductRepository.saving_product_variant_ids(product_variant_ids)

        self.ProductRepository.saving_product_data(product_data_list)
        
        self.ProductRepository.saving_varient_data(variant_data_list)


    def saving_shop_data_to_db_graphql(self, product_json):
        data = product_json['data']['products']['edges']
        product_data_list = []  
        variant_data_list = []  

        for product_edge in data:
            product = product_edge['node']
            product_data = {
                'id': int(re.search(r'\d+$', product['id']).group()),
                'title': product['title'],
                'description': product['bodyHtml'],
                'vendor': product['vendor'],
                'handle': product['handle'],
                'tags': product['tags'][0] if product['tags'] else None,
                'status': product['status'],
                'created_at': datetime.strptime(product['createdAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.strptime(product['updatedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S'),
                'image_url': product['images']['edges'][0]['node']['src'] if product['images']['edges'] else None,
                'type': list(product['productType'])
            }
            
            product_data_list.append(product_data)
            
            for variant_edge in product['variants']['edges']:
                variant = variant_edge['node']
                variant_data = {
                    'id': int(re.search(r'\d+$', variant['id']).group()),
                    'product_id': int(re.search(r'\d+$', product['id']).group()),  
                    'title': variant['title'],
                    'price': float(variant['price']),  
                    'inventory_quantity': variant['inventoryQuantity'],
                    'sku': variant['sku'],
                    'created_at': datetime.strptime(variant['createdAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.strptime(variant['updatedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S'),
                    'options': variant['selectedOptions'][0]['value'] if variant['selectedOptions'] else None
                }
                
                variant_data_list.append(variant_data)

        semattinc_search_model, product_variant_ids = self.SemanticSearchService.embeded_product((
                                                            product_data_list, variant_data_list))
        
        self.ProductRepository.saving_semantic_searching_model(semattinc_search_model)

        self.ProductRepository.saving_product_variant_ids(product_variant_ids)

        self.ProductRepository.saving_product_data_graphql(product_data_list)
        
        self.ProductRepository.saving_varient_data_graphql(variant_data_list)