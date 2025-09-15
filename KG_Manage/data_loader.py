import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DataLoader:


    def __init__(self, graph):
        self.graph = graph
        self.nodes = []
        self.rels = []

    def reload_db(self):

        if not self.graph:
            return False

        try:
            self.nodes.clear()
            self.rels.clear()


            node_query = "MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props"
            node_cursor = self.graph.run(node_query)

            for record in node_cursor:
                node_data = {
                    "id": record["id"],
                    "labels": list(record["labels"]),
                    "properties": dict(record["props"] or {})
                }
                self.nodes.append(node_data)


            rel_query = """
            MATCH (a)-[r]->(b) 
            RETURN elementId(r) AS rid, elementId(a) AS source, elementId(b) AS target, 
                   type(r) AS type, properties(r) AS props
            """
            rel_cursor = self.graph.run(rel_query)

            for record in rel_cursor:
                rel_data = {
                    "id": record["rid"],
                    "source": record["source"],
                    "target": record["target"],
                    "type": record["type"],
                    "properties": dict(record["props"] or {})
                }
                self.rels.append(rel_data)

            logger.info(f"Loaded {len(self.nodes)} nodes and {len(self.rels)} relationships")
            return True

        except Exception as e:
            logger.error(f"Failed to reload database: {e}")
            return False

    def get_graph_data(self):

        return {
            "nodes": self.nodes,
            "relationships": self.rels
        }

    def get_nodes_by_label(self, label: str) -> List[Dict[str, Any]]:

        query = f"""
        MATCH (n:`{label}`)
        RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props
        """

        nodes = []
        cursor = self.graph.run(query)
        for record in cursor:
            nodes.append({
                "id": record["id"],
                "labels": list(record["labels"]),
                "properties": dict(record["props"] or {})
            })
        return nodes

    def get_related_faces(self, structure_id: str) -> List[Dict[str, Any]]:

        query = f"""
        MATCH (structure)-[:HAS_FACE]-(face:Face)
        WHERE elementId(structure) = $structure_id
        RETURN DISTINCT elementId(face) AS id, labels(face) AS labels, properties(face) AS props
        ORDER BY face.face_no
        """

        faces = []
        cursor = self.graph.run(query, structure_id=structure_id)
        for record in cursor:
            faces.append({
                "id": record["id"],
                "labels": list(record["labels"]),
                "properties": dict(record["props"] or {})
            })
        return faces

    def get_relationships_for_structure(self, structure_id: str, face_ids: List[str]) -> List[Dict[str, Any]]:

        if not face_ids:
            return []

        face_ids_str = "', '".join(face_ids)
        query = f"""
        MATCH (a:Face)-[r:RELATIONSHIP]->(b:Face)
        WHERE elementId(a) IN ['{face_ids_str}'] AND elementId(b) IN ['{face_ids_str}']
        RETURN elementId(r) AS rid, elementId(a) AS source, elementId(b) AS target,
               type(r) AS type, properties(r) AS props
        """

        relationships = []
        cursor = self.graph.run(query)
        for record in cursor:
            relationships.append({
                "id": record["rid"],
                "source": record["source"],
                "target": record["target"],
                "type": record["type"],
                "properties": dict(record["props"] or {})
            })
        return relationships

    def get_available_labels(self) -> Dict[str, List[str]]:

        if not self.graph:
            return {}

        try:

            query = "MATCH (n) RETURN DISTINCT labels(n) AS labels"
            cursor = self.graph.run(query)

            all_labels = set()
            for record in cursor:
                labels = record["labels"]
                if labels:
                    all_labels.update(labels)


            categorized_labels = {
                "Step Labels": [],
                "Hole Labels": [],
                "Slot Labels": [],
                "Pocket Labels": [],
                "Passage Labels": [],
                "Other Labels": []
            }


            step_keywords = ["step", "Step"]
            hole_keywords = ["hole", "Hole"]
            slot_keywords = ["slot", "Slot"]
            pocket_keywords = ["pocket", "Pocket"]
            passage_keywords = ["passage", "Passage"]

            for label in sorted(all_labels):
                if any(keyword in label for keyword in step_keywords):
                    categorized_labels["Step Labels"].append(label)
                elif any(keyword in label for keyword in hole_keywords):
                    categorized_labels["Hole Labels"].append(label)
                elif any(keyword in label for keyword in slot_keywords):
                    categorized_labels["Slot Labels"].append(label)
                elif any(keyword in label for keyword in pocket_keywords):
                    categorized_labels["Pocket Labels"].append(label)
                elif any(keyword in label for keyword in passage_keywords):
                    categorized_labels["Passage Labels"].append(label)
                else:
                    categorized_labels["Other Labels"].append(label)

            return categorized_labels

        except Exception as e:
            logger.error(f"Failed to get label: {e}")
            return {}

    def debug_nodes(self) -> Dict[str, Any]:

        try:
            if not self.graph:
                return {"error": "Database not connected"}


            query = """
            MATCH (n) 
            RETURN elementId(n) as id, labels(n) as labels, properties(n) as props
            LIMIT 10
            """

            cursor = self.graph.run(query)
            results = []

            for record in cursor:
                results.append({
                    "id": record["id"],
                    "labels": list(record["labels"]),
                    "properties": dict(record["props"] or {})
                })

            return {
                "nodes": results,
                "count": len(results)
            }

        except Exception as e:
            import traceback
            return {
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def get_available_repositories(self) -> List[Dict[str, Any]]:

        if not self.graph:
            return []

        try:
            query = """
            MATCH (r:Repository)
            RETURN elementId(r) AS id, r.name AS name, properties(r) AS props
            ORDER BY r.name
            """
            cursor = self.graph.run(query)
            repositories = []

            for record in cursor:
                repositories.append({
                    "id": record["id"],
                    "name": record["name"],
                    "properties": dict(record["props"] or {})
                })

            return repositories

        except Exception as e:
            logger.error(f"Failed to get Repository list: {e}")
            return []


    def get_structures_by_repository(self, repository_id: str) -> Dict[str, List[str]]:

        if not self.graph:
            return {}

        try:
            query = """
            MATCH (r:Repository)-[:HAS_STRUCTURE]->(s)
            WHERE elementId(r) = $repository_id
            RETURN DISTINCT labels(s) AS labels
            """
            cursor = self.graph.run(query, repository_id=repository_id)

            all_labels = set()
            for record in cursor:
                labels = record["labels"]
                if labels:
                    all_labels.update(labels)


            categorized_labels = {
                "Step Labels": [],
                "Hole Labels": [],
                "Slot Labels": [],
                "Pocket Labels": [],
                "Passage Labels": [],
                "Other Labels": []
            }

            step_keywords = ["step", "Step"]
            hole_keywords = ["hole", "Hole"]
            slot_keywords = ["slot", "Slot"]
            pocket_keywords = ["pocket", "Pocket"]
            passage_keywords = ["passage", "Passage"]

            for label in sorted(all_labels):
                if any(keyword in label for keyword in step_keywords):
                    categorized_labels["Step Labels"].append(label)
                elif any(keyword in label for keyword in hole_keywords):
                    categorized_labels["Hole Labels"].append(label)
                elif any(keyword in label for keyword in slot_keywords):
                    categorized_labels["Slot Labels"].append(label)
                elif any(keyword in label for keyword in pocket_keywords):
                    categorized_labels["Pocket Labels"].append(label)
                elif any(keyword in label for keyword in passage_keywords):
                    categorized_labels["Passage Labels"].append(label)
                else:
                    categorized_labels["Other Labels"].append(label)

            return categorized_labels

        except Exception as e:
            logger.error(f"Failed to get Repository structure: {e}")
            return {}