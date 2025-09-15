import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class ExportManager:


    def __init__(self, graph, data_loader):
        self.graph = graph
        self.data_loader = data_loader

    def export_data(self) -> Dict[str, Any]:

        return {
            "nodes": [
                {
                    "id": n["id"],
                    "labels": n["labels"],
                    "properties": n["properties"]
                } for n in self.data_loader.nodes
            ],
            "relationships": [
                {
                    "id": r["id"],
                    "source": r["source"],
                    "target": r["target"],
                    "type": r["type"],
                    "properties": r.get("properties", {})
                } for r in self.data_loader.rels
            ],
            "exported_at": datetime.now().isoformat(),
            "version": "v8"
        }

    def selective_export(self, selected_labels: List[str]) -> Dict[str, Any]:

        if not self.graph:
            raise Exception("Database not connected")

        try:
            exported_nodes = []
            exported_relationships = []
            node_ids = set()


            for label in selected_labels:
                nodes = self.data_loader.get_nodes_by_label(label)
                for node in nodes:
                    if node["id"] not in node_ids:
                        exported_nodes.append(node)
                        node_ids.add(node["id"])


            if node_ids:
                node_ids_str = "', '".join(node_ids)
                query = f"""
                MATCH (main)-[:HAS_FACE]-(face:Face)
                WHERE elementId(main) IN ['{node_ids_str}']
                RETURN DISTINCT elementId(face) AS id, labels(face) AS labels, properties(face) AS props
                """

                cursor = self.graph.run(query)
                for record in cursor:
                    face_id = record["id"]
                    if face_id not in node_ids:
                        node_data = {
                            "id": face_id,
                            "labels": list(record["labels"]),
                            "properties": dict(record["props"] or {})
                        }
                        exported_nodes.append(node_data)
                        node_ids.add(face_id)


            if node_ids:
                node_ids_str = "', '".join(node_ids)
                query = f"""
                MATCH (a)-[r]->(b)
                WHERE elementId(a) IN ['{node_ids_str}'] AND elementId(b) IN ['{node_ids_str}']
                RETURN elementId(r) AS rid, elementId(a) AS source, elementId(b) AS target,
                       type(r) AS type, properties(r) AS props
                """

                cursor = self.graph.run(query)
                for record in cursor:
                    rel_data = {
                        "id": record["rid"],
                        "source": record["source"],
                        "target": record["target"],
                        "type": record["type"],
                        "properties": dict(record["props"] or {})
                    }
                    exported_relationships.append(rel_data)


            export_data = {
                "exported_at": datetime.now().isoformat(),
                "export_type": "selective",
                "selected_labels": selected_labels,
                "nodes": exported_nodes,
                "relationships": exported_relationships,
                "statistics": {
                    "total_nodes": len(exported_nodes),
                    "total_relationships": len(exported_relationships),
                    "selected_feature_nodes": len(
                        [n for n in exported_nodes if any(label in selected_labels for label in n["labels"])]),
                    "related_face_nodes": len([n for n in exported_nodes if "Face" in n["labels"]])
                },
                "version": "v8"
            }

            logger.info(f"Selective export complete: {len(exported_nodes)} Node, {len(exported_relationships)} Relationship")
            return export_data

        except Exception as e:
            logger.error(f"elective export failed: {e}")
            raise e

    def export_to_xml(self, selected_labels: Optional[List[str]] = None) -> str:

        if not self.graph:
            raise Exception("Database not connected")

        try:

            if selected_labels is None:
                all_labels_data = self.data_loader.get_available_labels()
                selected_labels = []
                for category_labels in all_labels_data.values():
                    selected_labels.extend(category_labels)


            root = ET.Element("StandardFeatureStructure")


            for label in selected_labels:

                query = f"""
                MATCH (n:Face)-[r:RELATIONSHIP]->(f:Face)
                WHERE n.structure_english_name = '{label}' AND f.structure_english_name = '{label}'
                RETURN n, r, f
                """

                cursor = self.graph.run(query)
                structures = {}

                for record in cursor:
                    n = record["n"]
                    r = record["r"]
                    f = record["f"]

                    structure_no = n.get("structure_no", "1")


                    if structure_no not in structures:
                        structures[structure_no] = {
                            "StructureNo": structure_no,
                            "StructureName": n.get("structure_name", ""),
                            "StructureEnglishName": n.get("structure_english_name", label),
                            "FaceList": [],
                            "RelationShipList": []
                        }


                    face_info_n = {
                        "FaceNo": n.get("face_no"),
                        "FaceType": n.get("face_type"),
                        "OutterLoopSize": n.get("outter_loop_size"),
                        "InnerLoopSize": n.get("inner_loop_size"),
                        "IsConvexSurface": n.get("is_convex_surface")
                    }
                    face_info_f = {
                        "FaceNo": f.get("face_no"),
                        "FaceType": f.get("face_type"),
                        "OutterLoopSize": f.get("outter_loop_size"),
                        "InnerLoopSize": f.get("inner_loop_size"),
                        "IsConvexSurface": f.get("is_convex_surface")
                    }


                    if face_info_n not in structures[structure_no]["FaceList"]:
                        structures[structure_no]["FaceList"].append(face_info_n)
                    if face_info_f not in structures[structure_no]["FaceList"]:
                        structures[structure_no]["FaceList"].append(face_info_f)


                    relationship_info = {
                        "SourceFaceNo": n.get("face_no"),
                        "TargetFaceNo": f.get("face_no"),
                        "IsIntersection": r.get("is_intersection"),
                        "IsParallel": r.get("is_parallel"),
                        "IsVertical": r.get("is_vertical"),
                        "IsConvexity": r.get("is_convexity"),
                        "SizeEdgeIntersection": r.get("size_edge_intersection"),
                        "RelationShipType": r.get("relationship_type"),
                        "FlagAngleDegree": r.get("flag_angle_degree")
                    }
                    structures[structure_no]["RelationShipList"].append(relationship_info)


                for structure in structures.values():
                    structure_elem = ET.SubElement(root, "Structure")
                    structure_elem.set("StructureNo", str(structure["StructureNo"]))
                    structure_elem.set("StructureName", str(structure["StructureName"]))
                    structure_elem.set("StructureEnglishName", str(structure["StructureEnglishName"]))

                    # FaceList
                    face_list_elem = ET.SubElement(structure_elem, "FaceList")
                    for face in structure["FaceList"]:
                        face_elem = ET.SubElement(face_list_elem, "Face")
                        face_elem.set("FaceNo", str(face["FaceNo"]))
                        face_elem.set("FaceType", str(face["FaceType"]))
                        face_elem.set("OutterLoopSize", str(face["OutterLoopSize"]))
                        face_elem.set("InnerLoopSize", str(face["InnerLoopSize"]) if face["InnerLoopSize"] else "")
                        face_elem.set("IsConvexSurface", str(face["IsConvexSurface"]))

                    # RelationShipList
                    rel_list_elem = ET.SubElement(structure_elem, "RelationShipList")
                    for relationship in structure["RelationShipList"]:
                        rel_elem = ET.SubElement(rel_list_elem, "RelationShip")
                        rel_elem.set("SourceFaceNo", str(relationship["SourceFaceNo"]))
                        rel_elem.set("TargetFaceNo", str(relationship["TargetFaceNo"]))
                        rel_elem.set("IsIntersection", str(relationship["IsIntersection"]))
                        rel_elem.set("IsParallel", str(relationship["IsParallel"]))
                        rel_elem.set("IsVertical", str(relationship["IsVertical"]))
                        rel_elem.set("IsConvexity", str(relationship["IsConvexity"]))
                        rel_elem.set("SizeEdgeIntersection", str(relationship["SizeEdgeIntersection"]) if relationship[
                            "SizeEdgeIntersection"] else "")
                        rel_elem.set("RelationShipType", str(relationship["RelationShipType"]))
                        rel_elem.set("FlagAngleDegree", str(relationship["FlagAngleDegree"]))


            xml_str = self.prettify_xml(root)

            logger.info(f"StandardFeatureStructure XML export completed")
            return xml_str

        except Exception as e:
            logger.error(f"XML export failed: {e}")
            raise e

    def selective_export_xml(self, selected_labels: List[str]) -> str:

        if not self.graph:
            raise Exception("Database not connected")

        try:

            all_structures = []
            for label in selected_labels:
                structures = self._get_structures_by_label_exact_format(label)
                all_structures.extend(structures)


            xml_content = self._generate_xml_exact_format(all_structures)

            logger.info(f"StandardFeatureStructure XML export completed")
            return xml_content

        except Exception as e:
            logger.error(f"XML export failed: {e}")
            raise e

    def selective_export_xml(self, selected_labels: List[str], repository_id: str = None) -> str:

        if not self.graph:
            raise Exception("Database not connected")

        try:

            root = ET.Element("StandardFeatureStructure")


            for label in selected_labels:

                if repository_id:
                    query = f"""
                    MATCH (r:Repository)-[:HAS_STRUCTURE]->(main)-[:HAS_FACE]->(n:Face)-[rel:RELATIONSHIP]->(f:Face)
                    WHERE elementId(r) = $repository_id 
                    AND n.structure_english_name = '{label}' 
                    AND f.structure_english_name = '{label}'
                    RETURN n, rel, f
                    """
                    cursor = self.graph.run(query, repository_id=repository_id)
                else:

                    query = f"""
                    MATCH (n:Face)-[r:RELATIONSHIP]->(f:Face)
                    WHERE n.structure_english_name = '{label}' AND f.structure_english_name = '{label}'
                    RETURN n, r, f
                    """
                    cursor = self.graph.run(query)

                structures = {}

                for record in cursor:
                    n = record["n"]
                    r = record["rel"]
                    f = record["f"]

                    structure_no = n.get("structure_no", "1")


                    if structure_no not in structures:
                        structures[structure_no] = {
                            "StructureNo": structure_no,
                            "StructureName": n.get("structure_name", ""),
                            "StructureEnglishName": n.get("structure_english_name", label),
                            "FaceList": [],
                            "RelationShipList": []
                        }


                    face_info_n = {
                        "FaceNo": n.get("face_no"),
                        "FaceType": n.get("face_type"),
                        "OutterLoopSize": n.get("outter_loop_size"),
                        "InnerLoopSize": n.get("inner_loop_size"),
                        "IsConvexSurface": n.get("is_convex_surface")
                    }
                    face_info_f = {
                        "FaceNo": f.get("face_no"),
                        "FaceType": f.get("face_type"),
                        "OutterLoopSize": f.get("outter_loop_size"),
                        "InnerLoopSize": f.get("inner_loop_size"),
                        "IsConvexSurface": f.get("is_convex_surface")
                    }


                    if face_info_n not in structures[structure_no]["FaceList"]:
                        structures[structure_no]["FaceList"].append(face_info_n)
                    if face_info_f not in structures[structure_no]["FaceList"]:
                        structures[structure_no]["FaceList"].append(face_info_f)


                    relationship_info = {
                        "SourceFaceNo": n.get("face_no"),
                        "TargetFaceNo": f.get("face_no"),
                        "IsIntersection": r.get("is_intersection"),
                        "IsParallel": r.get("is_parallel"),
                        "IsVertical": r.get("is_vertical"),
                        "IsConvexity": r.get("is_convexity"),
                        "SizeEdgeIntersection": r.get("size_edge_intersection"),
                        "RelationShipType": r.get("relationship_type"),
                        "FlagAngleDegree": r.get("flag_angle_degree")
                    }
                    structures[structure_no]["RelationShipList"].append(relationship_info)


                for structure in structures.values():
                    structure_elem = ET.SubElement(root, "Structure")
                    structure_elem.set("StructureNo", str(structure["StructureNo"]))
                    structure_elem.set("StructureName", str(structure["StructureName"]))
                    structure_elem.set("StructureEnglishName", str(structure["StructureEnglishName"]))

                    # FaceList
                    face_list_elem = ET.SubElement(structure_elem, "FaceList")
                    for face in structure["FaceList"]:
                        face_elem = ET.SubElement(face_list_elem, "Face")
                        face_elem.set("FaceNo", str(face["FaceNo"]))
                        face_elem.set("FaceType", str(face["FaceType"]))
                        face_elem.set("OutterLoopSize", str(face["OutterLoopSize"]))
                        face_elem.set("InnerLoopSize", str(face["InnerLoopSize"]) if face["InnerLoopSize"] else "")
                        face_elem.set("IsConvexSurface", str(face["IsConvexSurface"]))

                    # RelationShipList
                    rel_list_elem = ET.SubElement(structure_elem, "EdgeList")
                    for relationship in structure["RelationShipList"]:
                        rel_elem = ET.SubElement(rel_list_elem, "Edge")
                        rel_elem.set("SourceFaceNo", str(relationship["SourceFaceNo"]))
                        rel_elem.set("TargetFaceNo", str(relationship["TargetFaceNo"]))
                        rel_elem.set("IsIntersection", str(relationship["IsIntersection"]))
                        rel_elem.set("IsParallel", str(relationship["IsParallel"]))
                        rel_elem.set("IsVertical", str(relationship["IsVertical"]))
                        rel_elem.set("IsConvexity", str(relationship["IsConvexity"]))
                        rel_elem.set("SizeEdgeIntersection", str(relationship["SizeEdgeIntersection"]) if relationship[
                            "SizeEdgeIntersection"] else "")
                        rel_elem.set("RelationShipType", str(relationship["RelationShipType"]))
                        rel_elem.set("FlagAngleDegree", str(relationship["FlagAngleDegree"]))


            from xml.dom import minidom
            rough_string = ET.tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="    ")

            logger.info(f"StandardFeatureStructure XML export based on Repository is completed")
            return pretty_xml

        except Exception as e:
            logger.error(f"XML export failed·: {e}")
            raise e


    def _generate_xml_exact_format(self, structures: List[Dict[str, Any]]) -> str:

        root = ET.Element("StandardFeatureStructure")

        for structure in structures:
            structure_elem = ET.SubElement(root, "Structure", {
                "StructureNo": str(structure["StructureNo"]),
                "StructureName": str(structure["StructureName"]),
                "StructureEnglishName": str(structure["StructureEnglishName"])
            })

            # FaceList
            face_list_elem = ET.SubElement(structure_elem, "FaceList")
            for face in structure["FaceList"]:
                face_attrs = {
                    "FaceNo": str(face["FaceNo"]),
                    "FaceType": str(face["FaceType"]),
                    "OutterLoopSize": str(face["OutterLoopSize"]),
                    "InnerLoopSize": str(face["InnerLoopSize"]) if face["InnerLoopSize"] is not None else "",
                    "IsConvexSurface": str(face["IsConvexSurface"])
                }
                ET.SubElement(face_list_elem, "Face", face_attrs)

            # RelationShipList
            relationship_list_elem = ET.SubElement(structure_elem, "EdgeList")
            for relationship in structure["RelationShipList"]:
                rel_attrs = {
                    "SourceFaceNo": str(relationship["SourceFaceNo"]),
                    "TargetFaceNo": str(relationship["TargetFaceNo"]),
                    "IsIntersection": str(relationship["IsIntersection"]),
                    "IsParallel": str(relationship["IsParallel"]),
                    "IsVertical": str(relationship["IsVertical"]),
                    "IsConvexity": str(relationship["IsConvexity"]),
                    "SizeEdgeIntersection": str(relationship["SizeEdgeIntersection"]) if relationship[
                                                                                             "SizeEdgeIntersection"] is not None else "",
                    "RelationShipType": str(relationship["RelationShipType"]),
                    "FlagAngleDegree": str(relationship["FlagAngleDegree"])
                }
                ET.SubElement(relationship_list_elem, "Edge", rel_attrs)


        from xml.dom import minidom
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="    ")

        return pretty_xml

    def prettify_xml(self, elem: ET.Element) -> str:

        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")[23:]
        return pretty_xml