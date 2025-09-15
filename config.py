import os
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Config:



    APP_TITLE = "Feature recognition rule repository based on Neo4j"
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000


    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password_here")


    COLOR_PALETTE = [
        '#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F',
        '#EDC949', '#AF7AA1', '#FF9DA7', '#9C755F', '#BAB0AC'
    ]

    @staticmethod
    def get_env(key: str, default=None):

        val = os.getenv(key)
        return val if val is not None else default