import logging
import traceback
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RelationshipManager:


    def __init__(self, graph, data_loader):
        self.graph = graph
        self.data_loader = data_loader

    def create_rel(self, source_id: str, target_id: str, rel_type: str, properties: Dict[str, Any]) -> Dict[str, Any]:

        if not self.graph:
            raise Exception("Database not connected")

        try:

            logger.info(f"Creating relationship: {source_id} -[{rel_type}]-> {target_id}")
            logger.info(f"Properties: {properties}")


            source_cursor = self.graph.run(
                "MATCH (n) WHERE elementId(n) = $id RETURN count(n) as count",
                id=source_id
            )
            source_record = source_cursor.evaluate()

            target_cursor = self.graph.run(
                "MATCH (n) WHERE elementId(n) = $id RETURN count(n) as count",
                id=target_id
            )
            target_record = target_cursor.evaluate()

            if source_record == 0:
                raise Exception(f"Source node not found: {source_id}")

            if target_record == 0:
                raise Exception(f"Target node not found: {target_id}")


            safe_rel_type = rel_type.replace('`', '').replace("'", "").replace('"', '')


            query = f"""
            MATCH (a) WHERE elementId(a) = $source_id 
            MATCH (b) WHERE elementId(b) = $target_id 
            CREATE (a)-[r:`{safe_rel_type}`]->(b) 
            SET r += $props 
            RETURN elementId(r) AS id
            """

            logger.info(f"Executing query: {query}")

            result_cursor = self.graph.run(query,
                                           source_id=source_id,
                                           target_id=target_id,
                                           props=properties)

            rel_id = result_cursor.evaluate()

            if not rel_id:
                raise Exception("Failed to create relationship - no result returned")

            rel_data = {
                "id": rel_id,
                "source": source_id,
                "target": target_id,
                "type": rel_type,
                "properties": dict(properties)
            }

            self.data_loader.rels.append(rel_data)
            logger.info(f"Created relationship: {rel_id}")
            return rel_data

        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e

    def update_rel(self, rel_id: str, source_id: str, target_id: str, rel_type: str, properties: Dict[str, Any]) -> \
    Dict[str, Any]:

        if not self.graph:
            raise Exception("Database not connected")

        try:

            self.delete_rel(rel_id)


            new_rel = self.create_rel(source_id, target_id, rel_type, properties)

            logger.info(f"Updated relationship: {rel_id} -> {new_rel['id']}")
            return new_rel

        except Exception as e:
            logger.error(f"Error updating relationship: {e}")
            raise e

    def delete_rel(self, rel_id: str) -> bool:

        if not self.graph:
            raise Exception("Database not connected")

        try:
            self.graph.run(
                "MATCH ()-[e]->() WHERE elementId(e) = $id DELETE e",
                id=rel_id
            )


            self.data_loader.rels = [x for x in self.data_loader.rels if x["id"] != rel_id]

            logger.info(f"Deleted relationship: {rel_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting relationship: {e}")
            raise e