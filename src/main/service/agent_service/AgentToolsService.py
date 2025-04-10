from langchain.tools import tool
from src.main.repository.AgentRepository import ProductRepository
import re
from typing import Union

@tool
def get_product_types() -> list:
    """Returns a list of available product types from the database."""
    repo = ProductRepository()
    return [i[0] for i in repo.call_distinct_product_type()]

@tool
def find_products_flexible(query_or_criteria: Union[str, dict] = None) -> list:
    """
    Finds products based on a flexible query or search criteria. If no exact matches are found,
    it will return the closest matches when 'fallback' is set to True in the criteria.

    Args:
        query_or_criteria (Union[str, dict], optional): A search query string or a dictionary of search criteria.

    Returns:
        list: A list of dictionaries containing product details.
    """
    if query_or_criteria is None:
        query_or_criteria = {"fallback": True}  # Default to fallback logic if no input is provided

    repo = ProductRepository()
    products = repo.call_all_products_with_variants()  # No need for .mappings() here

    if isinstance(query_or_criteria, str):
        # Handle string-based query
        query = query_or_criteria.lower()
        keywords = set(re.findall(r'\w+', query))

        # Extract price range from the query
        price_matches = re.findall(r'\d+', query)
        price_min, price_max = None, None
        if len(price_matches) == 2:
            price_min, price_max = map(int, price_matches)
        elif len(price_matches) == 1:
            price_min = int(price_matches[0])
            price_max = price_min

        def score(product):
            title = product["title"].lower()
            product_type = product["product_type"].lower()
            price = float(product["price"])

            # Calculate relevance score based on keywords and price range
            keyword_score = sum(1 for word in keywords if word in title or word in product_type)
            price_score = 1 if (price_min is None or price_min <= price <= price_max) else 0

            return keyword_score + price_score

        ranked = sorted(products, key=score, reverse=True)
        best = [p for p in ranked if score(p) > 0]

    elif isinstance(query_or_criteria, dict):
        db = ProductRepository()
        # Handle dictionary-based criteria
        results = db.query_database(query_or_criteria)

        if not results and query_or_criteria.get("fallback"):
            # Fallback logic: Return least relevant products if no exact matches are found
            results = db.query_database({"relevance": "low"})

        best = results

    # Ensure results are formatted with 'shopify_id' and other necessary fields
    formatted_results = [
        {
            "shopify_id": str(p["shopify_id"]),
            "title": p["title"],
            "product_type": p["product_type"],
            "price": str(p["price"]),
            "status": p["status"]
        }
        for p in best[:10]
    ]

    return formatted_results
