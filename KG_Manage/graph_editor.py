import logging
from typing import Dict, List, Any, Optional
from config import Config
from database_manager import DatabaseManager
from data_loader import DataLoader
from node_manager import NodeManager
from relationship_manager import RelationshipManager
from KG_Manage.export_manager import ExportManager
from KG_Manage.import_manager import ImportManager

logger = logging.getLogger(__name__)


class Neo4jGraphEditor:

    def __init__(self):

        self.db_manager = DatabaseManager()
        self.data_loader = DataLoader(self.db_manager.graph)
        self.node_manager = NodeManager(self.db_manager.graph, self.data_loader)
        self.relationship_manager = RelationshipManager(self.db_manager.graph, self.data_loader)
        self.export_manager = ExportManager(self.db_manager.graph, self.data_loader)
        self.import_manager = ImportManager(self.db_manager.graph, self.data_loader)


        self.palette = Config.COLOR_PALETTE
        self.label_colors = {}
        self.rel_colors = {}


        if self.db_manager.graph:
            self.data_loader.reload_db()

    @property
    def graph(self):

        return self.db_manager.graph

    @property
    def nodes(self):

        return self.data_loader.nodes

    @property
    def rels(self):

        return self.data_loader.rels


    def connect_db(self):

        return self.db_manager.connect_db()

    def reload_db(self):

        return self.data_loader.reload_db()

    def test_connection(self):

        return self.db_manager.test_connection()

    def get_health_status(self):

        return self.db_manager.get_health_status()

    def reconnect(self):

        result = self.db_manager.reconnect()
        if result["success"]:
            self.data_loader.reload_db()
        return result


    def get_graph_data(self):

        return self.data_loader.get_graph_data()

    def get_available_labels(self):

        return self.data_loader.get_available_labels()

    def debug_nodes(self):

        return self.data_loader.debug_nodes()


    def create_node(self, labels: List[str], properties: Dict[str, Any]):

        return self.node_manager.create_node(labels, properties)

    def update_node(self, node_id: str, labels: List[str], properties: Dict[str, Any]):

        return self.node_manager.update_node(node_id, labels, properties)

    def delete_node(self, node_id: str):

        return self.node_manager.delete_node(node_id)

    def node_display_full(self, node: Dict[str, Any]):

        return self.node_manager.node_display_full(node)


    def create_rel(self, source_id: str, target_id: str, rel_type: str, properties: Dict[str, Any]):

        return self.relationship_manager.create_rel(source_id, target_id, rel_type, properties)

    def update_rel(self, rel_id: str, source_id: str, target_id: str, rel_type: str, properties: Dict[str, Any]):

        return self.relationship_manager.update_rel(rel_id, source_id, target_id, rel_type, properties)

    def delete_rel(self, rel_id: str):

        return self.relationship_manager.delete_rel(rel_id)


    def export_data(self):

        return self.export_manager.export_data()

    def selective_export(self, selected_labels: List[str]):

        return self.export_manager.selective_export(selected_labels)

    def export_to_xml(self, selected_labels: Optional[List[str]] = None):

        return self.export_manager.export_to_xml(selected_labels)

    def selective_export_xml(self, selected_labels: List[str], repository_id: str = None):

        return self.export_manager.selective_export_xml(selected_labels, repository_id)


    def import_data(self, data: Dict[str, Any]):

        return self.import_manager.import_data(data)

    def clean_import_data(self, data: Dict[str, Any]):

        return self.import_manager.clean_import_data(data)

    def import_from_xml(self, xml_content: str, repository_name: str = None):

        return self.import_manager.import_from_xml(xml_content, repository_name)


    def env(self, key: str, default=None):

        return Config.get_env(key, default)

    def get_available_repositories(self):

        return self.data_loader.get_available_repositories()

    def get_structures_by_repository(self, repository_id: str):

        return self.data_loader.get_structures_by_repository(repository_id)