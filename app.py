from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from datetime import datetime
import json
import logging
import traceback

from config import Config
from KG_Manage.graph_editor import Neo4jGraphEditor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

editor = Neo4jGraphEditor()



@app.route('/')
def index():

    return render_template('neo4j_editor.html')


@app.route('/api/health')
def health_check():

    return jsonify(editor.get_health_status())


@app.route('/api/reconnect', methods=['POST'])
def reconnect_database():

    result = editor.reconnect()
    return jsonify(result)


@app.route('/api/test-connection', methods=['GET'])
def test_connection():

    return jsonify(editor.test_connection())



@app.route('/api/graph', methods=['GET'])
def get_graph_data():

    try:
        if editor.graph:
            editor.reload_db()

        data = editor.get_graph_data()
        return jsonify({
            "nodes": data["nodes"],
            "relationships": data["relationships"],
            "success": True
        })
    except Exception as e:
        logger.error(f"Error getting graph data: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


@app.route('/api/labels', methods=['GET'])
def get_labels():
    try:
        labels = editor.get_available_labels()
        return jsonify({
            "success": True,
            "labels": labels
        })
    except Exception as e:
        logger.error(f"Failed to get label: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


@app.route('/api/debug/nodes', methods=['GET'])
def debug_nodes():
    try:
        result = editor.debug_nodes()
        return jsonify(result)
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500



@app.route('/api/nodes', methods=['POST'])
def create_node():
    try:
        data = request.get_json()
        labels = data.get('labels', ['Node'])
        properties = data.get('properties', {})

        if isinstance(labels, str):
            labels = [l.strip() for l in labels.split(',') if l.strip()]

        if not labels:
            labels = ['Node']

        node = editor.create_node(labels, properties)

        return jsonify({
            "node": node,
            "success": True,
            "message": "Node created successfully"
        })

    except Exception as e:
        logger.error(f"Error creating node: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


@app.route('/api/nodes/<node_id>', methods=['PUT'])
def update_node(node_id):

    try:
        data = request.get_json()
        labels = data.get('labels', ['Node'])
        properties = data.get('properties', {})

        if isinstance(labels, str):
            labels = [l.strip() for l in labels.split(',') if l.strip()]

        if not labels:
            labels = ['Node']

        editor.update_node(node_id, labels, properties)

        updated_node = None
        for node in editor.nodes:
            if node["id"] == node_id:
                updated_node = node
                break

        return jsonify({
            "node": updated_node,
            "success": True,
            "message": "Node updated"
        })

    except Exception as e:
        logger.error(f"Error updating node: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


@app.route('/api/nodes/<node_id>', methods=['DELETE'])
def delete_node_route(node_id):
    try:
        logger.info(f"Received a request to delete a node: {node_id}")

        result = editor.delete_node(node_id)

        return jsonify({
            "success": True,
            "message": "Node deleted"
        })

    except Exception as e:
        logger.error(f"Error deleting node: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500



@app.route('/api/relationships', methods=['POST'])
def create_relationship():

    try:
        data = request.get_json()
        logger.info(f"Received relationship creation request: {data}")

        source_id = data.get('source_id')
        target_id = data.get('target_id')
        rel_type = data.get('type', 'RELATED')
        properties = data.get('properties', {})

        if not source_id or not target_id:
            error_msg = "Missing source_id or target_id"
            logger.error(error_msg)
            return jsonify({
                "error": error_msg,
                "success": False,
                "details": f"source_id: {source_id}, target_id: {target_id}"
            }), 400

        if not rel_type or not rel_type.strip():
            rel_type = 'RELATED'

        relationship = editor.create_rel(source_id, target_id, rel_type, properties)

        return jsonify({
            "relationship": relationship,
            "success": True,
            "message": "New relationship successfully added"
        })

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error creating relationship: {error_msg}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

        return jsonify({
            "error": error_msg,
            "success": False,
            "traceback": traceback.format_exc() if app.debug else None
        }), 500


@app.route('/api/relationships/<rel_id>', methods=['PUT'])
def update_relationship(rel_id):
    try:
        data = request.get_json()
        source_id = data.get('source_id')
        target_id = data.get('target_id')
        rel_type = data.get('type', 'RELATED')
        properties = data.get('properties', {})

        if not source_id or not target_id:
            return jsonify({
                "error": "Missing source_id or target_id",
                "success": False
            }), 400

        relationship = editor.update_rel(rel_id, source_id, target_id, rel_type, properties)

        return jsonify({
            "relationship": relationship,
            "success": True,
            "message": "Relationship updated successfully"
        })

    except Exception as e:
        logger.error(f"Error updating relationship: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


@app.route('/api/relationships/<rel_id>', methods=['DELETE'])
def delete_relationship(rel_id):
    try:
        editor.delete_rel(rel_id)

        return jsonify({
            "success": True,
            "message": "Relationship deleted"
        })

    except Exception as e:
        logger.error(f"Error deleting relationship: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500



@app.route('/api/export', methods=['GET'])
def export_graph():
    try:
        format_type = request.args.get('format', 'xml').lower()

        if format_type == 'xml':
            xml_content = editor.export_to_xml()
            return Response(
                xml_content,
                mimetype='application/xml',
                headers={
                    'Content-Disposition': f'attachment; filename=neo4j_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml'
                }
            )
        else:
            return jsonify({
                "error": "Only supports XML format export",
                "success": False
            }), 400

    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


@app.route('/api/export/xml/full', methods=['GET'])
def export_full_xml():
    try:
        xml_content = editor.export_to_xml()

        return Response(
            xml_content,
            mimetype='application/xml',
            headers={
                'Content-Disposition': f'attachment; filename=neo4j_full_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml'
            }
        )

    except Exception as e:
        logger.error(f"Full XML export failed: {e}")
        return jsonify({
            "error": str(e),
            "success": False,
            "traceback": traceback.format_exc() if app.debug else None
        }), 500


@app.route('/api/export/xml/selective', methods=['POST'])
def export_selective_xml():
    try:
        data = request.get_json()
        selected_labels = data.get('labels', [])
        repository_id = data.get('repository_id')

        if not selected_labels:
            return jsonify({
                "error": "Please select at least one tag",
                "success": False
            }), 400

        xml_content = editor.selective_export_xml(selected_labels, repository_id)

        return Response(
            xml_content,
            mimetype='application/xml',
            headers={
                'Content-Disposition': f'attachment; filename=selective_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml'
            }
        )

    except Exception as e:
        logger.error(f"Selective XML export fails: {e}")
        return jsonify({
            "error": str(e),
            "success": False,
            "traceback": traceback.format_exc() if app.debug else None
        }), 500


@app.route('/api/export/xml', methods=['POST'])
def export_xml():
    try:
        data = request.get_json()
        selected_labels = data.get('labels', [])

        if not selected_labels:
            return jsonify({
                "error": "Please select at least one tag",
                "success": False
            }), 400

        xml_content = editor.selective_export_xml(selected_labels)

        return Response(
            xml_content,
            mimetype='application/xml',
            headers={
                'Content-Disposition': f'attachment; filename=feature_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml'
            }
        )

    except Exception as e:
        logger.error(f"XML export failed: {e}")
        return jsonify({
            "error": str(e),
            "success": False,
            "traceback": traceback.format_exc() if app.debug else None
        }), 500



@app.route('/api/import', methods=['POST'])
def import_graph():
    try:
        if 'file' in request.files:
            file = request.files['file']
            repository_name = request.form.get('repository_name', '').strip()

            if file.filename == '':
                return jsonify({
                    "error": "No file selected",
                    "success": False
                }), 400

            if not repository_name:
                return jsonify({
                    "error": "Please provide a repository name",
                    "success": False
                }), 400

            filename = file.filename.lower()

            try:
                if filename.endswith('.xml'):
                    xml_content = file.read().decode('utf-8')
                    result = editor.import_from_xml(xml_content, repository_name)

                    return jsonify({
                        "success": True,
                        "message": f"XML import completed: {result['nodes_created']} nodes, {result['relationships_created']} relationships, Repository: {repository_name}",
                        "details": result
                    })
                else:
                    return jsonify({
                        "error": "Unsupported file format, please upload an XML file",
                        "success": False
                    }), 400

            except UnicodeDecodeError:
                return jsonify({
                    "error": "File encoding error, please ensure the file is UTF-8 encoded",
                    "success": False
                }), 400

        else:
            return jsonify({
                "error": "Please upload a file",
                "success": False
            }), 400

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Import failed: {error_msg}")
        logger.error(f"Full error information: {traceback.format_exc()}")

        return jsonify({
            "error": error_msg,
            "success": False,
            "traceback": traceback.format_exc() if app.debug else None
        }), 500


@app.route('/api/repositories', methods=['GET'])
def get_repositories():
    try:
        result = editor.get_available_repositories()
        return jsonify({
            "success": True,
            "repositories": result
        })
    except Exception as e:
        logger.error(f"Failed to get the repository list: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


@app.route('/api/repositories/<repository_id>/structures', methods=['GET'])
def get_repository_structures(repository_id):
    try:
        structures = editor.get_structures_by_repository(repository_id)
        return jsonify({
            "success": True,
            "labels": structures
        })
    except Exception as e:
        logger.error(f"Failed to obtain the Repository structure: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

if __name__ == '__main__':
    print(f"""
🚀 {Config.APP_TITLE}

📁 HTML file location: templates/neo4j_editor.html
🌐 Access Address: http://localhost:{Config.PORT}
🔗 Neo4j Connection: {Config.NEO4J_URI}

Environment Variable Configuration:
- NEO4J_URI: {Config.NEO4J_URI}
- NEO4J_USER: {Config.NEO4J_USER}
- NEO4J_PASSWORD: {'Set' if Config.NEO4J_PASSWORD else 'Not set, using default value'}

Database connection status: {'✅ Connected' if editor.graph else '❌ Connection failed'}
Number of nodes: {len(editor.nodes)}
Number of relationships: {len(editor.rels)}
""")

    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)