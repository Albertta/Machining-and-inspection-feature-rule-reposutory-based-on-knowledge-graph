from py2neo import Graph
import logging
from config import Config

logger = logging.getLogger(__name__)


class DatabaseManager:


    def __init__(self):
        self.graph = None
        self.connect_db()

    def connect_db(self):

        try:
            self.graph = Graph(
                Config.NEO4J_URI,
                auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
            )

            self.graph.run("RETURN 1").evaluate()
            logger.info(f"Connected to Neo4j at {Config.NEO4J_URI}")
            return True
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            self.graph = None
            return False

    def test_connection(self):

        try:
            if not self.graph:
                return {
                    "connected": False,
                    "error": "Graph instance not initialized"
                }


            test_result = self.graph.run("RETURN 1 as test").evaluate()


            db_cursor = self.graph.run("CALL dbms.components()")
            db_info = db_cursor.data()

            return {
                "connected": True,
                "test_result": test_result,
                "database_info": db_info,
                "neo4j_version": db_info[0]["versions"][0] if db_info else "Unknown"
            }

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "connected": False,
                "error": str(e)
            }

    def get_health_status(self):

        return {
            "status": "ok",
            "database_connected": self.graph is not None,
            "app_title": Config.APP_TITLE
        }

    def reconnect(self):

        success = self.connect_db()
        return {
            "success": success,
            "message": "Reconnected successfully" if success else "Reconnection failed"
        }