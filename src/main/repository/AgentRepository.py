from src.main.repository.db_connector import DBConnection
import sqlalchemy as sa
from sqlalchemy import Table, MetaData
from sqlalchemy.exc import SQLAlchemyError
import logging



logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ProductRepository:
    def __init__(self):
        self.db_connection = DBConnection()
        self.engine = self.db_connection.get_engine()
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)

    def call_all_products_with_variants(self):
        try:
            with self.engine.connect() as conn:
                products = Table('products_synonym', self.metadata, autoload_with=self.engine)
                variants = Table('variants_synonym', self.metadata, autoload_with=self.engine)
                query = (
                    sa.select(products, variants)
                    .join(variants, products.c.id == variants.c.product_id)
                )
                result = conn.execute(query)
                return result.mappings()  # Return a Result object with mappings
        except SQLAlchemyError as e:
            logging.error(f"Error fetching products with variants: {e}")
            return []

    def call_distinct_product_type(self):
        try:
            products = Table("product_synonym", self.metadata, autoload_with=self.engine)
            query = sa.select(products.c.product_type).distinct()
            with self.engine.connect() as conn:
                result = conn.execute(query)
                return result.fetchall()
        except SQLAlchemyError as e:
            logging.error(f"Error fetching distinct product types: {e}")
            return []

    def query_database(self, criteria: dict):
        """
        Queries the database for products based on the given criteria.

        Args:
            criteria (dict): A dictionary containing search filters (e.g., product type, price range).

        Returns:
            list: A list of dictionaries containing product details.
        """
        try:
            products = Table("products_synonym", self.metadata, autoload_with=self.engine)
            variants = Table("variants_synonym", self.metadata, autoload_with=self.engine)

            # Build query dynamically based on criteria
            filters = []
            if "product_type" in criteria:
                filters.append(products.c.product_type == criteria["product_type"])
            if "price_min" in criteria:
                filters.append(variants.c.price >= criteria["price_min"])
            if "price_max" in criteria:
                filters.append(variants.c.price <= criteria["price_max"])
            if "relevance" in criteria and criteria["relevance"] == "low":
                filters.append(True)  # No strict filters for fallback

            # Combine filters into a query
            query = sa.select(
                products.c.shopify_id.label("shopify_id"),
                products.c.title,
                products.c.product_type,
                variants.c.price,
                products.c.status
            ).join(
                variants, products.c.id == variants.c.product_id
            ).where(sa.and_(*filters)).limit(10)

            # Execute the query
            with self.engine.connect() as conn:
                result = conn.execute(query)
                rows = [
                    {
                        "shopify_id": row.shopify_id,
                        "title": row.title,
                        "product_type": row.product_type,
                        "price": row.price,
                        "status": row.status,
                    }
                    for row in result.mappings()  # Use mappings() to return rows as dictionaries
                ]

                # If no rows are found, fetch 3 random products
                if not rows:
                    logging.warning("No matches found. Fetching random fallback products.")
                    fallback_query = sa.select(
                        products.c.id.label("shopify_id"),
                        products.c.title,
                        products.c.product_type,
                        variants.c.price,
                        products.c.status
                    ).join(
                        variants, products.c.id == variants.c.product_id
                    ).order_by(sa.func.random()).limit(3)  # Fetch 3 random products
                    fallback_result = conn.execute(fallback_query)
                    rows = [
                        {
                            "shopify_id": row.shopify_id,
                            "title": row.title,
                            "product_type": row.product_type,
                            "price": row.price,
                            "status": row.status,
                        }
                        for row in fallback_result.mappings()
                    ]

                return rows
        except SQLAlchemyError as e:
            logging.error(f"Error querying database with criteria {criteria}: {e}")
            return []