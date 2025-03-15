from src.main.repository.db_connector import DBConnection
import sqlalchemy as sa
from sqlalchemy import create_engine, Table, MetaData
import logging
from typing import List

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class SemanticSearchRepository:
    def __init__(self):
        self.db_connection = DBConnection()
        self.engine = self.db_connection.get_engine()
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine) 

    def saving_semantic_searching_model(self,model):
        semantic_model = Table('semantic_model', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.insert(semantic_model).values(
                    model=model
                    )
                conn.execute(stmt)  
                logging.debug("Semantic model saved successfully!")

    def call_semantic_search_model(self):
        semantic_model = Table('semantic_model', self.metadata, autoload_with=self.engine)

        with self.engine.connect() as conn:
            with conn.begin():
                stmt = sa.select(semantic_model).order_by(
                    semantic_model.c.insert_date.desc()).limit(1)
                result = conn.execute(stmt)
                return result.fetchone()[1]

    

