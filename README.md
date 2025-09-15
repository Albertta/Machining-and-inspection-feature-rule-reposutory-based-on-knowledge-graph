# Machining-and-inspection-feature-rule-reposutory-based-on-knowledge-graph
A comprehensive web-based feature rule knowledge graph management system was developed using Neo4j, Flask, and modern web technologies. This tool provides an intuitive interface for creating, editing, visualizing, and managing the feature rule knowledge graph library.
<img width="2549" height="1367" alt="image" src="https://github.com/user-attachments/assets/e58125a0-72ad-48cf-ba6f-4a8261854f3c" />

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
- **Option A: Neo4j Desktop (Recommended)** \
  Download and install Neo4j Desktop
  Create a new database project
  Set password (configure in config.py)
  Start the database
- **Option B: Neo4j Docker**
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
# 🧩 Repostiory Structure
```text
neo4j-KG-Manager/
├── app.py
├── config.py
├── KG_Manage/
│   ├── graph_editor.py
│   ├── database_manager.py
│   ├── data_loader.py
│   ├── node_manager.py
│   ├── relationship_manager.py
│   ├── export_manager.py
│   └── import_manager.py
├── templates/
│   └── neo4j_editor.html
└── examples/
    └── sample_structure.xml
├── README.md
├── LICENSE
```

# 🗺️ Quick Start
**1.Start the Application**
 ```bash
   python app.py
 ```
The application will be available at http://localhost:5000 \

**2.Verify Database Connection**
- Check the connection status indicator in the top-right corner
- Green dot indicates successful connection
- Use the **"Reconnect"** button if connection fails
<img width="2549" height="1367" alt="image" src="https://github.com/user-attachments/assets/405304ef-286f-4239-a5a9-eeb94893967f" />

\
**3.Basic Operation**
 - **Create Nodes:** \
   a. Click **"ADD Node"** button \
   b. Specify labels (comma-separated) \
   c. Add properties as key-value pairs \
   d. Click **"Confirm"**

- **Create Relationships:** \
  a. Click **"ADD Relationship"** button \
  b. Select source and target nodes \
  c. Specify relationship type \
  d. Add properties if needed \
  e. Click **"Confirm"**

- **Import Data:**
  a. Click **"Import ▼"** → "Import XML File" \
  b. Provide repository name \
  c. Select XML file (sample_structure.xml) \
  d. Click **"Start Import"**
  
# API Endpoints
All API endpoints are defined in app.py. The Flask application provides the following **REST API:** 
**1. Graph Operations**
- GET /api/graph - Retrieve all graph data
- GET /api/health - Health check
- POST /api/reconnect - Reconnect to database

**2. Node Operations**
- POST /api/nodes - Create new node
- PUT /api/nodes/<node_id> - Update node
- DELETE /api/nodes/<node_id> - Delete node

**3. Relationship Operations**
- POST /api/relationships - Create relationship

  
 





