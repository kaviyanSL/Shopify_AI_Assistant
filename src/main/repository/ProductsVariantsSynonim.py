from src.main.repository.db_connector import DBConnection
import os
import sqlalchemy as sa
from sqlalchemy import create_engine, Table, MetaData
import logging
from typing import List
import json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ProductsVariantsSynonim:
    def __init__(self):
        self.db_connection = DBConnection()
        self.engine = self.db_connection.get_engine()
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine) 

    def call_products_synonym(self):
        products_synonym = Table('products_synonym', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.select(products_synonym)
                result = conn.execute(stmt)
                return result.fetchall()
    
    def call_variants_synonym(self):
        variants_synonym = Table('variants_synonym', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.select(variants_synonym)
                result = conn.execute(stmt)
                return result.fetchall()