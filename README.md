# Machining-and-inspection-feature-rule-reposutory-based-on-knowledge-graph
A comprehensive web-based feature rule knowledge graph management system was developed using Neo4j, Flask, and modern web technologies. This tool provides an intuitive interface for creating, editing, visualizing, and managing the feature rule knowledge graph library.

# 🚀 Features

- **Interactive Graph Visualization**
  - Real-time graph rendering with **ECharts** integration
  - Supports zooming, dragging, and highlighting
  - Dynamic updates for rule editing and deletion

- **Knowledge Graph Management**
  - Create, edit, and delete rules with an intuitive interface
  - Merge and reuse graph elements seamlessly
  - Attribute-level modification with **Cypher** support

- **Web-based System**
  - Built with **Neo4j**, **Flask**, and modern web technologies
  - Cross-platform and browser-friendly
  - RESTful API for external system integration

- **User-Friendly Interface**
  - Clean and interactive UI design
  - Dark/light theme switching
  - Real-time search and filtering of graph elements

# 🌿 Requirements  
- Python==3.9.18
- Flask==3.0.3
- Flask-CORS==6.0.1
- py2neo==2021.2.3

# 🗄️ Neo4j Database Setup
- Option A: Neo4j Desktop (Recommended) \
  Download and install Neo4j Desktop
  Create a new database project
  Set password (configure in config.py)
  Start the database
- Option B: Neo4j Docker
```bash
  docker run  --name neo4j-kg  -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/yourpassword neo4j:latest
```
# 🧱 Environment Configuration
- Configure directly in **config.py**:
```markdown
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_password_here"
```
# Quich Start
```bash
  python app.py
```
 The application will be available at: http://localhost:5000 





