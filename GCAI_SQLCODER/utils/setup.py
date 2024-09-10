import os
import logging
import pandas as pd
import json
import urllib3
import re
from dotenv import load_dotenv
from sqlalchemy import create_engine, text as sql_text
from utils.ollama_custom import Ollama
from utils.chromadb_vector_custom import ChromaDB_VectorStore
from utils.embedding_function import OllamaEmbeddingFunction
from utils.constants import LOG_FORMAT


logging.basicConfig(format=LOG_FORMAT,level=logging.DEBUG)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
log = logging.getLogger(__name__)
load_dotenv()

class MyVanna(ChromaDB_VectorStore, Ollama):
    """
    Custom class to configure Ollama and ChromaDB
    """
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)


def data_engine():
    """
    Create Oracle Autonomous Database connection engine using SQLAlchemy.\n
    returns - connection engine
    """
    user = os.getenv("user")
    password = os.getenv("password")
    dsn = os.getenv("dsn")
    config_dir = os.getenv("config_dir")
    wallet_location = os.getenv("wallet_location")
    wallet_password = os.getenv("wallet_password")

    connection_args = {
        "user": user,
        "password": password,
        "dsn": dsn,
        "config_dir": config_dir,
        "wallet_location": wallet_location,
        "wallet_password": wallet_password,
    }

    engine = create_engine(
    'oracle+oracledb://:@',
    connect_args=connection_args,pool_size=5,pool_recycle=1800,pool_timeout=120)
    return engine


def run_sql_query(sql: str, **kwargs) -> pd.DataFrame:
    """
    Executes SQL query and retrieves data from Oracle Autonomous Database.
    returns - Dataframe Object
    """
    # log.info("\n"*3,"-"*25,sql.strip().replace("\n", " "),"-"*25)
    sql = sql.strip().rstrip(";")
    log.info(sql_text(sql))
    try:
        engine = data_engine()
        with engine.connect() as connection:
            result = connection.execute(sql_text(sql))
            connection.close()
            return pd.DataFrame(result.fetchall(), columns=list(result.keys()))
    except Exception as e:
        log.error(f"Error occurred while executing SQL Query: {e}")
        return None


def setup_connexion():
    """
    Instantialise Vanna, connect with Ollama LLM Server and initialise Ollama embedding function
    """
    ollama_server_uri = os.getenv("ollama_server")
    ollama_model_name = os.getenv("ollama_model")
    ollama_secondary_model_name = os.getenv("ollama_secondary_model") or None
    vector_db_path = os.getenv("vector_db_path")
    embedding_function = OllamaEmbeddingFunction(model_name= ollama_model_name)
    vn = MyVanna(config=
                 {
                     'model': ollama_model_name,
                     'secondary_model': ollama_secondary_model_name,
                     'ollama_host': ollama_server_uri,
                     'path': vector_db_path, 
                     'n_results': 15,
                     'embedding_function': embedding_function
                 }
                )
    # This gives the package a function that it can use to run the SQL
    vn.run_sql = run_sql_query
    vn.run_sql_is_set = True
    return vn
