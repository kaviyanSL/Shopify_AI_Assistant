from src.main.repository.db_connector import DBConnection
import os
import sqlalchemy as sa
from sqlalchemy import create_engine, Table, MetaData
import logging

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
