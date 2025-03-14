from src.main.repository.db_connector import DBConnection
import os
import sqlalchemy as sa
from sqlalchemy import create_engine, Table, MetaData
import logging
from typing import List
import json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ProductRepository:
    def __init__(self):
        self.db_connection = DBConnection()
        self.engine = self.db_connection.get_engine()
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine) 

    def saving_product_data(self, product_data_list):
        products = Table('products', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.insert(products)
                conn.execute(stmt, product_data_list)  
                logging.debug("Products saved successfully!")
                

    def saving_varient_data(self,varients_data_list):
        variants = Table('variants', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.insert(variants)
                conn.execute(stmt, varients_data_list)  
                logging.debug("Varients saved successfully!")

    def saving_semantic_searching_model(self,model):
        semantic_model = Table('semantic_model', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.insert(semantic_model).values(
                    model=model
                    )
                conn.execute(stmt)  
                logging.debug("Semantic model saved successfully!")

    def saving_product_variant_ids(self, list_of_product_variant_ids):
        product_variant_ids = Table('product_variant_ids', self.metadata, autoload_with=self.engine)

        try:
            with self.engine.connect() as conn:
                with conn.begin() as transaction:
                    try:
                        for idx, product_variant in list_of_product_variant_ids:
                            stmt = sa.insert(product_variant_ids).values(
                                id=idx,
                                product_variant_ids=json.dumps(product_variant),
                            )
                            conn.execute(stmt)
                            logging.debug(f"Product variant ID {idx} saved successfully!")
                    except Exception as e:
                        transaction.rollback()  
                        logging.error(f"Error saving product variant ID {idx}: {e}")
                        raise  
        except Exception as e:
            logging.error(f"Database connection error: {e}")


    def saving_product_data_graphql(self, product_data_list):
        products = Table('products', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.insert(products)
                conn.execute(stmt, product_data_list)  
                logging.debug("Products saved successfully!")
                

    def saving_varient_data_graphql(self,varients_data_list):
        variants = Table('variants', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.insert(variants)
                conn.execute(stmt, varients_data_list)  
                logging.debug("Varients saved successfully!")

    def call_semantic_search_model(self):
        semantic_model = Table('semantic_model', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.select(semantic_model).order_by(
                    semantic_model.c.insert_date.desc()).limit(1)
                result = conn.execute(stmt)
                return result.fetchone()[1]
            
    def product_variant_ids_call(self,list_of_ids):
        product_variant_ids = Table('product_variant_ids', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.select(product_variant_ids).where(
                    product_variant_ids.c.id.in_(list_of_ids.tolist())
                )
                result = conn.execute(stmt)
                return result.fetchall()
            
    def call_products(self,id):
        products = Table('products', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.select(products).where(
                    products.c.id.in_(id)
                )
                result = conn.execute(stmt)
                return result.fetchall()
            
    def call_variants(self,id):
        variants = Table('variants', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.select(variants).where(
                    variants.c.id.in_(id)
                )
                result = conn.execute(stmt)
                return result.fetchall()

