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
                return result.fetchall()
        except SQLAlchemyError as e:
            logging.error(f"Error fetching products with variants: {e}")
            return []

    def call_distinct_product_type(self):
        try:
            products = Table("product_synonym", self.metadata, autoload=True, autoload_with=self.engine)
            query = sa.select(products.c.product_type).distinct()
            with self.engine.connect() as conn:
                result = conn.execute(query)
                return result.fetchall()
        except SQLAlchemyError as e:
            logging.error(f"Error fetching distinct product types: {e}")
            return []

    # def call_products(self, status, product_type, max_price):
    #     try:
    #         products = Table('products', self.metadata, autoload=True, autoload_with=self.engine)
    #         variants = Table('variants', self.metadata, autoload=True, autoload_with=self.engine)
    #         query = (
    #             sa.select(products)
    #             .join(variants, products.c.id == variants.c.product_id)
    #             .where(
    #                 products.c.status == status,
    #                 products.c.product_type == product_type,
    #                 variants.c.price <= max_price
    #             )
    #         )
    #         with self.engine.connect() as conn:
    #             result = conn.execute(query)
    #             return result.fetchall()
    #     except SQLAlchemyError as e:
    #         logging.error(f"Error fetching products: {e}")
    #         return []