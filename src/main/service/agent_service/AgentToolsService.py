from langchain.tools import tool
from src.main.repository.AgentRepository import ProductRepository
import re

@tool
def get_product_types() -> list:
    """Returns a list of available product types from the database."""
    repo = ProductRepository()
    return [i[0] for i in repo.call_distinct_product_type()]

@tool
def find_products_flexible(query: str) -> list:
    """
    Finds products based on a flexible query.

    Args:
        query (str): The search query containing keywords.

    Returns:
        list: A list of dictionaries containing product details.
    """
    repo = ProductRepository()
    products = repo.call_all_products_with_variants()
    query = query.lower()
    keywords = set(re.findall(r'\w+', query))

    def score(product):
        title = getattr(product, "title", "")
        body_html = getattr(product, "body_html", "")
        product_type = getattr(product, "product_type", "")
        vendor = getattr(product, "vendor", "")
        handle = getattr(product, "handle", "")
        price = getattr(product, "price", "")

        text = f"{title} {body_html} {product_type} {vendor} {handle} {price}".lower()
        return sum(1 for word in keywords if word in text)

    def get_price(p):
        return getattr(p, "price", "")

    ranked = sorted(products, key=score, reverse=True)
    best = [p for p in ranked if score(p) > 0]

    return [
        {   
            "shopify_id": p.shopify_id,
            "title": p.title,
            "product_type": p.product_type,
            "price": get_price(p),
            "status": p.status
        }
        for p in best[:10]
    ]

