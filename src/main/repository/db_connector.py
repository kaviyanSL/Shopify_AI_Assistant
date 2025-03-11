import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DBConnection:
    _instance = None
    _engine = None
    _Session = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBConnection, cls).__new__(cls)
            cls._engine = create_engine("mysql+pymysql://root:root@localhost:3306/shopify_search_assistant",
                                        pool_size=200,          
                                        max_overflow=20,       
                                        pool_timeout=30,       
                                        pool_recycle=1800 )
            cls._Session = sessionmaker(bind=cls._engine)
        return cls._instance

    def get_session(self):
        return self._Session()

    def get_engine(self):
        return self._engine