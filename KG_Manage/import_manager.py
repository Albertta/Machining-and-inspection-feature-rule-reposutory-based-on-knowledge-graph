import json
import xml.etree.ElementTree as ET
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ImportManager:


    def __init__(self, graph, data_loader):
        self.graph = graph
        self.data_loader = data_loader

    def import_data(self, data: Dict[str, Any]) -> bool:

        if not self.graph:
            raise Exception("Database not connected")

        try:
            logger.info("Starting data validation and cleaning...")
            id_map = {}
            created_nodes = 0
            created_rels = 0
            skipped_rels = 0


            nodes_data = data.get("nodes", [])
            logger.info(f"Prepare to import {len(nodes_data)} Nodes")

            for i, node_data in enumerate(nodes_data):
                try:
                    labels = node_data.get("labels") or ["Node"]
                    props = dict(node_data.get("properties") or {})


                    props = {k: v for k, v in props.items() if v != "" and v is not None}

                    labels_str = "".join([f":`{label}`" for label in labels])
                    query = f"CREATE (m{labels_str}) SET m += $p RETURN elementId(m) AS id"

                    cursor = self.graph.run(query, p=props)
                    new_id = cursor.evaluate()

                    if new_id:
                        old_id = node_data.get("id")
                        if old_id:
                            id_map[old_id] = new_id
                        created_nodes += 1

                        if (i + 1) % 10 == 0:
                            logger.info(f"Created {i + 1}/{len(nodes_data)} Nodes")
                    else:
                        logger.warning(f"Node creation failed: {node_data}")

                except Exception as e:
                    logger.error(f"Error creating node: {e}, Node data: {node_data}")
                    continue

            logger.info(f"Node import completed: {created_nodes}/{len(nodes_data)}")


            rels_data = data.get("relationships", [])
            logger.info(f"Prepare to import {len(rels_data)} Relationships")


            created_rel_pairs = set()

            for i, rel_data in enumerate(rels_data):
                try:
                    old_source = rel_data.get("source")
                    old_target = rel_data.get("target")
                    rel_type = rel_data.get("type") or "RELATED"
                    props = dict(rel_data.get("properties") or {})


                    props = {k: v for k, v in props.items() if v != "" and v is not None}


                    if old_source not in id_map or old_target not in id_map:
                        logger.warning(f"Skip relationship: node does not exist {old_source} -> {old_target}")
                        skipped_rels += 1
                        continue

                    new_source = id_map[old_source]
                    new_target = id_map[old_target]


                    if new_source == new_target:
                        logger.warning(f"Skip self-loop relationship: {rel_type} on {new_source}")
                        skipped_rels += 1
                        continue



                    safe_rel_type = rel_type.replace('`', '').replace("'", "").replace('"', '')

                    query = f"""
                        MATCH (x) WHERE elementId(x) = $a 
                        MATCH (y) WHERE elementId(y) = $b 
                        CREATE (x)-[rel:`{safe_rel_type}`]->(y) 
                        SET rel += $p
                        """

                    self.graph.run(query, a=new_source, b=new_target, p=props)

                    created_rels += 1

                    if (i + 1) % 50 == 0:
                        logger.info(f"Processed {i + 1}/{len(rels_data)} Relationships")

                except Exception as e:
                    logger.error(f"Error creating relationship: {e}, Relational data: {rel_data}")
                    skipped_rels += 1
                    continue

            logger.info(f"Relationship import completed: Create {created_rels}，Skip {skipped_rels}")


            self.data_loader.reload_db()

            logger.info(f"Import Complete - Node: {created_nodes}, Relationship: {created_rels}, Skip: {skipped_rels}")
            return True

        except Exception as e:
            logger.error(f"Error importing data: {e}")
            logger.error(f"Full error message: {traceback.format_exc()}")
            raise e

    def clean_import_data(self, data: Dict[str, Any]) -> Dict[str, Any]:

        cleaned_data = {
            "nodes": [],
            "relationships": []
        }


        seen_node_ids = set()
        for node in data.get("nodes", []):
            node_id = node.get("id")
            if node_id and node_id not in seen_node_ids:

                props = node.get("properties", {})
                cleaned_props = {k: v for k, v in props.items() if v != "" and v is not None}

                cleaned_node = {
                    "id": node_id,
                    "labels": node.get("labels", ["Node"]),
                    "properties": cleaned_props
                }
                cleaned_data["nodes"].append(cleaned_node)
                seen_node_ids.add(node_id)


        seen_rels = set()
        node_ids = {node["id"] for node in cleaned_data["nodes"]}

        for rel in data.get("relationships", []):
            source = rel.get("source")
            target = rel.get("target")
            rel_type = rel.get("type", "RELATED")


            if source in node_ids and target in node_ids and source != target:
                rel_key = (source, target, rel_type)
                if rel_key not in seen_rels:

                    props = rel.get("properties", {})
                    cleaned_props = {k: v for k, v in props.items() if v != "" and v is not None}

                    cleaned_rel = {
                        "source": source,
                        "target": target,
                        "type": rel_type,
                        "properties": cleaned_props
                    }
                    cleaned_data["relationships"].append(cleaned_rel)
                    seen_rels.add(rel_key)

        return cleaned_data

    def import_from_xml(self, xml_content: str, repository_name: str = None) -> Dict[str, int]:

        if not self.graph:
            raise Exception("Database not connected")

        try:
            logger.info("Start XML data import...")


            try:
                root = ET.fromstring(xml_content)
            except ET.ParseError as e:
                raise Exception(f"XML format error: {e}")


            if root.tag == "StandardFeatureStructure":
                return self._import_standard_feature_structure(root, repository_name)
            elif root.tag == "Neo4jGraphData":
                return self._import_neo4j_graph_data(root, repository_name)
            else:
                raise Exception(f"Unsupported XML format, the root element is: {root.tag}")

        except Exception as e:
            logger.error(f"XML import failed: {e}")
            raise e

    def _import_standard_feature_structure(self, root: ET.Element, repository_name: str = None) -> Dict[str, int]:

        created_nodes = 0
        created_rels = 0
        skipped_rels = 0

        try:

            repository_id = None
            if repository_name:
                repository_props = {
                    "name": repository_name,
                    "type": "Repository",
                    "created_at": datetime.now().isoformat()
                }


                repo_query = "CREATE (r:Repository) SET r += $props RETURN elementId(r) AS id"
                repo_cursor = self.graph.run(repo_query, props=repository_props)
                repository_id = repo_cursor.evaluate()
                if repository_id:
                    created_nodes += 1
                    logger.info(f"Creating a Repository Node: {repository_id}")


            for structure_elem in root.findall("Structure"):
                structure_no = structure_elem.get("StructureNo", "1")
                structure_name = structure_elem.get("StructureName", "")
                structure_english_name = structure_elem.get("StructureEnglishName", "")


                structure_labels = [structure_english_name] if structure_english_name else ["Structure"]
                structure_props = {
                    "structure_no": structure_no,
                    "structure_name": structure_name,
                    "structure_english_name": structure_english_name
                }

                labels_str = "".join([f":`{label}`" for label in structure_labels])
                query = f"CREATE (n{labels_str}) SET n += $props RETURN elementId(n) AS id"
                cursor = self.graph.run(query, props=structure_props)
                structure_id = cursor.evaluate()

                if structure_id:
                    created_nodes += 1
                    logger.info(f"Create the main structure node: {structure_id}")


                    if repository_id and structure_id:
                        has_structure_query = """
                        MATCH (r) WHERE elementId(r) = $repository_id
                        MATCH (s) WHERE elementId(s) = $structure_id
                        CREATE (r)-[:HAS_STRUCTURE]->(s)
                        """
                        self.graph.run(has_structure_query, repository_id=repository_id, structure_id=structure_id)
                        created_rels += 1


                face_list = structure_elem.find("FaceList")
                face_id_map = {}

                if face_list is not None:
                    for face_elem in face_list.findall("Face"):
                        face_no = face_elem.get("FaceNo", "0")


                        face_props = {
                            "face_no": face_no,
                            "face_type": face_elem.get("FaceType", "0"),
                            "outter_loop_size": face_elem.get("OutterLoopSize", "1"),
                            "inner_loop_size": face_elem.get("InnerLoopSize", "0"),
                            "is_convex_surface": face_elem.get("IsConvexSurface", "0"),
                            "structure_no": structure_no,
                            "structure_english_name": structure_english_name,
                            "color": "#000000"
                        }


                        if face_props["inner_loop_size"] == "":
                            face_props["inner_loop_size"] = "0"


                        face_query = "CREATE (f:Face) SET f += $props RETURN elementId(f) AS id"
                        face_cursor = self.graph.run(face_query, props=face_props)
                        face_id = face_cursor.evaluate()

                        if face_id:
                            face_id_map[face_no] = face_id
                            created_nodes += 1


                            if structure_id:
                                has_face_query = """
                                MATCH (s) WHERE elementId(s) = $structure_id
                                MATCH (f) WHERE elementId(f) = $face_id
                                CREATE (s)-[:HAS_FACE]->(f)
                                """
                                self.graph.run(has_face_query, structure_id=structure_id, face_id=face_id)
                                created_rels += 1


                rel_list = structure_elem.find("EdgeList")
                if rel_list is None:

                    rel_list = structure_elem.find("RelationShipList")

                if rel_list is not None:

                    rel_elements = rel_list.findall("Edge")
                    if not rel_elements:

                        rel_elements = rel_list.findall("RelationShip")

                    for rel_elem in rel_elements:
                        source_face_no = rel_elem.get("SourceFaceNo")
                        target_face_no = rel_elem.get("TargetFaceNo")

                        if source_face_no in face_id_map and target_face_no in face_id_map:
                            source_id = face_id_map[source_face_no]
                            target_id = face_id_map[target_face_no]


                            if source_id == target_id:
                                skipped_rels += 1
                                continue


                            rel_props = {
                                "is_intersection": rel_elem.get("IsIntersection", "1"),
                                "is_parallel": rel_elem.get("IsParallel", "0"),
                                "is_vertical": rel_elem.get("IsVertical", "1"),
                                "is_convexity": rel_elem.get("IsConvexity", "-1"),
                                "size_edge_intersection": rel_elem.get("SizeEdgeIntersection", "1"),
                                "relationship_type": rel_elem.get("RelationShipType", "1"),
                                "flag_angle_degree": rel_elem.get("FlagAngleDegree", "1"),
                                "color": "#000000"
                            }


                            if rel_props["size_edge_intersection"] == "":
                                rel_props["size_edge_intersection"] = "1"


                            rel_query = """
                            MATCH (a) WHERE elementId(a) = $source_id
                            MATCH (b) WHERE elementId(b) = $target_id
                            CREATE (a)-[r:RELATIONSHIP]->(b)
                            SET r += $props
                            """
                            self.graph.run(rel_query, source_id=source_id, target_id=target_id, props=rel_props)
                            created_rels += 1
                        else:
                            skipped_rels += 1
                            logger.warning(f"Skip relationship: Face node does not exist {source_face_no} -> {target_face_no}")


            self.data_loader.reload_db()

            logger.info(
                f"StandardFeatureStructure import completed - Node: {created_nodes}, Relationship: {created_rels}, Skip: {skipped_rels}")
            return {
                "nodes_created": created_nodes,
                "relationships_created": created_rels,
                "relationships_skipped": skipped_rels
            }

        except Exception as e:
            logger.error(f"StandardFeatureStructure import failed: {e}")
            raise e