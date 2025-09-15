import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class NodeManager:


    def __init__(self, graph, data_loader):
        self.graph = graph
        self.data_loader = data_loader

    def create_node(self, labels: List[str], properties: Dict[str, Any]) -> Dict[str, Any]:

        if not self.graph:
            raise Exception("Database not connected")

        try:

            labels_str = "".join([f":`{label}`" for label in labels])
            query = f"CREATE (n{labels_str}) SET n += $props RETURN elementId(n) AS id"

            cursor = self.graph.run(query, props=properties)
            node_id = cursor.evaluate()

            if not node_id:
                raise Exception("Failed to create node - no result returned")

            node_data = {
                "id": node_id,
                "labels": labels,
                "properties": dict(properties)
            }

            self.data_loader.nodes.append(node_data)
            logger.info(f"Created node: {node_id}")
            return node_data

        except Exception as e:
            logger.error(f"Error creating node: {e}")
            raise e

    def update_node(self, node_id: str, labels: List[str], properties: Dict[str, Any]) -> bool:

        if not self.graph:
            raise Exception("Database not connected")

        try:

            current_labels = self.get_node_labels(node_id)
            if current_labels:
                remove_labels = []
                for label in current_labels:
                    remove_labels.append(f"n:`{label}`")
                clear_labels_query = f"MATCH (n) WHERE elementId(n) = $id REMOVE {', '.join(remove_labels)}"
                self.graph.run(clear_labels_query, id=node_id)


            self.graph.run(
                "MATCH (n) WHERE elementId(n) = $id SET n = $props",
                id=node_id, props=properties
            )


            for label in labels:
                self.graph.run(
                    f"MATCH (n) WHERE elementId(n) = $id SET n:`{label}`",
                    id=node_id
                )


            for node in self.data_loader.nodes:
                if node["id"] == node_id:
                    node["labels"] = labels
                    node["properties"] = dict(properties)
                    break

            logger.info(f"Updated node: {node_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating node: {e}")
            raise e

    def delete_node(self, node_id: str) -> bool:

        if not self.graph:
            raise Exception("Database not connected")

        try:

            self.graph.run(
                "MATCH (x) WHERE elementId(x) = $id DETACH DELETE x",
                id=node_id
            )


            self.data_loader.nodes = [x for x in self.data_loader.nodes if x["id"] != node_id]
            self.data_loader.rels = [r for r in self.data_loader.rels if
                                     r["source"] != node_id and r["target"] != node_id]

            logger.info(f"Deleted node: {node_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting node: {e}")
            raise e

    def get_node_labels(self, node_id: str) -> List[str]:

        try:
            cursor = self.graph.run(
                "MATCH (n) WHERE elementId(n) = $id RETURN labels(n) AS labels",
                id=node_id
            )
            records = cursor.data()
            return records[0]["labels"] if records else []
        except:
            return []

    def node_display_full(self, node: Dict[str, Any]) -> str:

        props = node["properties"]
        title = (props.get("name") or
                 props.get("english_name") or
                 (node["labels"][0] if node["labels"] else "Node"))
        return f"{title} [{node['id']}]"