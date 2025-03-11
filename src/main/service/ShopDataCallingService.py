import requests
import os
import pandas as pd
from dotenv import load_dotenv
import logging
from src.main.repository.ProductRepository import ProductRepository
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


load_dotenv()

class ShopDataCallingService:
    def __init__(self):
        self.ProductRepository = ProductRepository()
    
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
        product_data_list = []  # List to store product data dictionaries
        variant_data_list = []  # List to store variant data dictionaries

        # Loop through each product and create a dictionary for each one
        for product in data['products']:
            # Create product data dictionary
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
                'image_url': product['image']['src']  
            }
            
            # Append the product data to the list
            product_data_list.append(product_data)
            
            # Loop through the variants of each product
            for variant in product['variants']:
                # Create variant data dictionary
                variant_data = {
                    'id': variant['id'],
                    'product_id': product['id'],  
                    'title': variant['title'],
                    'price': float(variant['price']),  
                    'inventory_quantity': variant['inventory_quantity'],
                    'sku': variant['sku'],
                    'created_at': variant['created_at'],
                    'updated_at': variant['updated_at']
                }
                
                
                variant_data_list.append(variant_data)
        
        self.ProductRepository.saving_product_data(product_data_list)
        
        self.ProductRepository.saving_varient_data(variant_data_list)
