import requests
import os
import pandas as pd
from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


load_dotenv()

class ShopDataCallingService:
    def __init__(self,product_category):
        self.product_category = product_category
    
    def calling_data(self):
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

        return df_grouped.get_group(f"{self.product_category}").to_dict()

