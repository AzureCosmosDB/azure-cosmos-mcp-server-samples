# Azure Cosmos DB MCP Server + Intelligent Query Assistant

**A complete Python-based MCP (Model Context Protocol) ecosystem for Azure Cosmos DB** - featuring a streamable HTTP server, an intelligent ReAct agent client, and a beautiful Streamlit UI for natural language querying.

## What is this?

This project provides three powerful components:

1. **🚀 MCP Server**: Streamable HTTP server exposing Cosmos DB operations via MCP protocol
2. **🤖 Intelligent Client**: ReAct agent with LangChain for natural language queries
3. **🎨 Streamlit UI**: Beautiful web interface for non-technical users

Think of it as a complete stack for AI-powered database interactions - from protocol to UI!


## ✨ What's New in v0.3.0

### MCP Server Enhancements
- 🌐 **Streamable HTTP Transport**: Modern, scalable HTTP/JSON protocol
- 📦 **FastMCP 2.3.0**: Latest FastMCP with enhanced stability
- 🔄 **JSON Responses**: All tools return structured JSON for better parsing
- 📋 **Enhanced Tools**: Improved count_documents with filter support
- 🚀 **Configurable Host/Port**: Flexible deployment options

### Intelligent Client
- 🤖 **ReAct Agent**: LangChain-powered reasoning and action loop
- 🔍 **Sequential Location Fallback**: Smart field cascade (City → Region → Area)
- ⚡ **Guardrails**: Safe query wrappers prevent common errors
- 🎯 **Temporal Intelligence**: Natural date parsing ("last month", "this year")
- 🛡️ **Latest Guard**: Optional versioning support (c.latest = 0)
- 📊 **Configurable Settings**: Customize iterations, TOP N, fallback fields

### Streamlit UI
- 🎨 **Modern Interface**: Clean, responsive web UI
- 📊 **Multiple Views**: Table, JSON, and column-select modes
- 📥 **CSV Export**: Download query results
- 📜 **Query History**: Search, filter, and rerun past queries
- 🔧 **Agent Steps**: View reasoning process (optional)
- ⚡ **Quick Actions**: One-click schema, count, and sample queries
- 🎯 **Live Metrics**: Execution time, step count, result count

## Architecture

```
┌─────────────────────┐
│  Streamlit UI       │  Port 8501 (Web Interface)
│  streamlit_app.py   │  • Natural language input
└──────────┬──────────┘  • Visual data display
           │              • Query history
           ▼              • CSV export
┌─────────────────────┐
│  Intelligent Client │  (Python Process)
│  cosmos_client.py   │  • ReAct Agent
└──────────┬──────────┘  • LangChain
           │              • Smart fallbacks
           │              • Query optimization
           ▼
┌─────────────────────┐
│  MCP Server         │  Port 8000 (HTTP/JSON)
│  cosmos_mcp_server  │  • Streamable HTTP
└──────────┬──────────┘  • FastMCP
           │              • Tool execution
           ▼
┌─────────────────────┐
│  Azure Cosmos DB    │
│  (Cloud Database)   │
└─────────────────────┘
```

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Component Details](#component-details)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Available Tools](#available-tools)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Prerequisites

Before you begin, ensure you have:
- ✅ **Python 3.8+** (Python 3.10+ recommended)
- ✅ **Azure Cosmos DB** account with:
  - Account URI
  - Access Key
  - Database name
  - Container name
- ✅ **Azure OpenAI** access (for intelligent client):
  - Endpoint URL
  - API Key
  - Deployment name (e.g., gpt-4o)
- ✅ **Operating System**: Windows, macOS, or Linux

## Installation

### Quick Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/cosmos-mcp-assistant.git
cd cosmos-mcp-assistant
```

2. **Create virtual environment:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create environment configuration:**
Create a `.env` file in the project root:

```env
# Azure Cosmos DB Configuration
COSMOS_URI=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-primary-key
COSMOS_DATABASE=your-database-name
COSMOS_CONTAINER=your-container-name

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-05-01-preview

# MCP Server Configuration
MCP_HOST=localhost
MCP_PORT=8000
MCP_URL=http://localhost:8000/mcp
```

## Quick Start

### Option 1: Full Stack (Recommended for End Users)

**Terminal 1 - Start MCP Server:**
```bash
python cosmos_mcp_server.py
```

**Terminal 2 - Start Streamlit UI:**
```bash
streamlit run streamlit_app.py
```

**Access the UI:**
Open browser to `http://localhost:8501`

### Option 2: CLI Client (For Developers)

**Terminal 1 - Start MCP Server:**
```bash
python cosmos_mcp_server.py
```

**Terminal 2 - Run CLI Client:**
```bash
python cosmos_client.py
```

### Option 3: MCP Server Only (For LLM Integration)

```bash
python cosmos_mcp_server.py --host localhost --port 8000
```

Connect with any MCP-compatible client at `http://localhost:8000/mcp`

## Component Details

### 🚀 MCP Server (`cosmos_mcp_server.py`)

**Purpose**: Expose Cosmos DB operations via MCP protocol

**Features**:
- ✅ Streamable HTTP transport (JSON-RPC over HTTP)
- ✅ 10 powerful tools (query, count, schema, etc.)
- ✅ Cross-partition query support
- ✅ Optional Managed Identity authentication
- ✅ Configurable host/port
- ✅ Health check endpoint

**Usage**:
```bash
# Basic start
python server.py

# Custom host/port
python server.py --host 0.0.0.0 --port 8080

# With Managed Identity
python server.py --use-managed-identity

# With all options
python server.py \
  --uri https://account.documents.azure.com:443/ \
  --key your-key \
  --db mydb \
  --container mycontainer \
  --host localhost \
  --port 8000
```

**Endpoints**:
- `http://localhost:8000/mcp` - Main MCP endpoint
- `http://localhost:8000/health` - Health check (if implemented)

### 🤖 Intelligent Client (`client.py`)

**Purpose**: Natural language query interface with intelligent reasoning

**Key Features**:
- ✅ **ReAct Agent**: Reasoning and action loop with LangChain
- ✅ **Smart Fallbacks**: Sequential location field cascade
- ✅ **Temporal Parsing**: Understands "last month", "this year", etc.
- ✅ **Query Guardrails**: Automatic SQL fence stripping, latest guard injection
- ✅ **Configurable**: Max iterations, TOP N, location fields

**Configuration Options**:
```python
from client import CosmosClient, Settings

# Customize settings
cfg = Settings(
    # Azure OpenAI
    azure_endpoint="https://resource.openai.azure.com/",
    azure_api_key="your-key",
    azure_deployment="gpt-4o",
    
    # MCP Connection
    mcp_url="http://localhost:8000/mcp",
    
    # Agent Behavior
    max_iterations=4,
    default_top_n=50,
    enforce_latest_guard=False,  # Set True for versioned data
    
    # Location Fallback (priority order)
    location_fallback_fields=["City", "Region", "Area", "District"]
)

client = CosmosClient(cfg)
await client.connect()
```

**Usage**:
```python
# Simple query
response = await client.ainvoke("How many documents are in the container?")
print(response['text'])

# Complex query
response = await client.ainvoke(
    "Show me all active properties in Miami from last month"
)
```

### 🎨 Streamlit UI (`streamlit_app.py`)

**Purpose**: User-friendly web interface for querying Cosmos DB

**Features**:
- ✅ **Natural Language Input**: Ask questions in plain English
- ✅ **Multiple Display Modes**: Table, JSON, column-select
- ✅ **Query History**: Search, filter, rerun past queries
- ✅ **CSV Export**: Download results with one click
- ✅ **Agent Reasoning**: View intermediate steps (optional)
- ✅ **Quick Actions**: Schema, count, sample with one click
- ✅ **Live Metrics**: Execution time, steps, result count
- ✅ **Configurable**: Adjust agent settings in real-time

**UI Sections**:
1. **Sidebar**: Connection, settings, quick actions
2. **Query Input**: Text area with example queries
3. **Results Display**: Tables, JSON, metrics
4. **Query History**: Searchable past queries

## Configuration

### Environment Variables (`.env`)

```env
# ============================================================================
# Azure Cosmos DB Configuration
# ============================================================================
COSMOS_URI=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-primary-key-here
COSMOS_DATABASE=your-database-name
COSMOS_CONTAINER=your-default-container

# ============================================================================
# Azure OpenAI Configuration (for Intelligent Client & Streamlit)
# ============================================================================
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-05-01-preview

# ============================================================================
# MCP Server Configuration
# ============================================================================
MCP_HOST=localhost
MCP_PORT=8000
MCP_URL=http://localhost:8000/mcp
```

### Streamlit Secrets (`.streamlit/secrets.toml`)

```toml
# For production Streamlit deployments
AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
AZURE_OPENAI_API_KEY = "your-api-key-here"
AZURE_OPENAI_DEPLOYMENT = "gpt-4o"
MCP_URL = "http://localhost:8000/mcp"
```

### Agent Configuration (Python)

```python
# Customize in cosmos_client.py or programmatically
cfg = Settings(
    # Agent Controls
    max_iterations=4,           # Max reasoning steps
    agent_timeout=60,           # Overall timeout (seconds)
    tool_timeout=45,            # Per-tool timeout
    
    # Query Behavior
    default_top_n=50,           # Default LIMIT for queries
    enforce_latest_guard=False, # Add c.latest = 0 filter
    enable_sql_count_fallback=True,  # Fallback to SQL COUNT
    
    # Location Fallback (try in order)
    location_fallback_fields=["City", "Region", "Area"],
    
    # Connection
    connect_timeout=10,
    mcp_url="http://localhost:8000/mcp"
)
```

## Usage Examples

### Natural Language Queries

**Schema Exploration:**
```
"Describe the container schema"
"What fields are available?"
"Show me the partition key"
```

**Counting:**
```
"How many documents are in the container?"
"Count documents where Status = 'Active'"
"How many records from last month?"
```

**Data Retrieval:**
```
"Show me 10 sample documents"
"Find all records where City is Miami"
"List top 20 items ordered by price descending"
```

**Filtering:**
```
"Show active properties in Miami"
"Find documents with Price > 500000"
"Get all records from last year"
```

**Distinct Values:**
```
"List all distinct cities"
"What are the unique status values?"
"Show me all product categories"
```

**Temporal Queries:**
```
"Show sales from this month"
"Count orders from last 30 days"
"Find records created this year"
```

### Programmatic Usage

```python
import asyncio
from cosmos_client import CosmosClient, Settings

async def main():
    # Configure client
    cfg = Settings(
        azure_endpoint="https://resource.openai.azure.com/",
        azure_api_key="your-key",
        mcp_url="http://localhost:8000/mcp"
    )
    
    client = CosmosClient(cfg)
    await client.connect()
    
    # Execute queries
    queries = [
        "How many documents are there?",
        "Show me 5 sample records",
        "List all distinct cities"
    ]
    
    for query in queries:
        response = await client.ainvoke(query)
        print(f"\nQ: {query}")
        print(f"A: {response['text']}")
        print(f"Time: {response['elapsed_sec']}s")

asyncio.run(main())
```

## Available Tools

The MCP server exposes these tools:

| Tool | Description | Example |
|------|-------------|---------|
| `query_cosmos` | Execute SQL queries | `SELECT * FROM c WHERE c.City = 'Miami'` |
| `count_documents` | Count with filters | `{"filters": {"Status": "Active"}}` |
| `list_collections` | List all containers | N/A |
| `describe_container` | Show schema | Optional: container name |
| `get_sample_documents` | Preview data | `limit=5` |
| `list_distinct_values` | Get unique values | `field_name="City"` |
| `find_implied_links` | Find relationships | N/A |
| `get_partition_key_info` | Get partition key | N/A |
| `get_indexing_policy` | View indexing | N/A |

### Tool Response Format

All tools return JSON:

```json
{
  "count": 10,
  "results": [...],
  "container": "container-name"
}
```

## Deployment

### Local Development

```bash
# Terminal 1: MCP Server
python cosmos_mcp_server.py

# Terminal 2: Streamlit UI
streamlit run streamlit_app.py
```

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start both server and Streamlit
CMD ["sh", "-c", "python server.py & streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0"]
```

**Build and Run:**
```bash
docker build -t cosmos-mcp-assistant .
docker run -p 8000:8000 -p 8501:8501 --env-file .env cosmos-mcp-assistant
```

### Cloud Deployment (Azure Container Instances)

```bash
# Build and push to Azure Container Registry
az acr build --registry myregistry \
  --image cosmos-mcp-assistant:latest .

# Deploy to ACI
az container create \
  --resource-group mygroup \
  --name cosmos-mcp \
  --image myregistry.azurecr.io/cosmos-mcp-assistant:latest \
  --ports 8000 8501 \
  --environment-variables \
    COSMOS_URI="https://..." \
    COSMOS_KEY="..." \
    AZURE_OPENAI_ENDPOINT="https://..." \
    AZURE_OPENAI_API_KEY="..."
```

## Troubleshooting

### Common Issues

**1. MCP Server won't start**
```bash
# Check if port is in use
netstat -an | grep 8000

# Try different port
python server.py --port 8001
```

**2. Client can't connect to server**
```bash
# Verify server is running
curl http://localhost:8000/mcp

# Check MCP_URL in .env
echo $MCP_URL

# Test with verbose logging
python client.py --verbose
```

**3. Streamlit connection issues**
- Ensure MCP server is running first
- Check sidebar connection status
- Verify Azure OpenAI credentials
- Check browser console for errors

**4. Azure OpenAI errors**
```
Error: 401 Unauthorized
→ Check AZURE_OPENAI_API_KEY

Error: 404 Not Found
→ Verify AZURE_OPENAI_DEPLOYMENT name

Error: Rate limit exceeded
→ Wait or upgrade your Azure OpenAI tier
```

**5. Agent not finding results**
- Try relaxing filters (use LIKE instead of =)
- Check schema with "Describe container"
- View intermediate steps in Streamlit
- Verify data exists with "Show sample documents"

### Debug Mode

**Enable verbose logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Streamlit debug:**
```bash
streamlit run streamlit_app.py --logger.level=debug
```

**Agent intermediate steps:**
Enable "Show Intermediate Steps" in Streamlit sidebar

## Security Best Practices

### 🔒 Production

1. **Use Managed Identity:**
```bash
python server.py --use-managed-identity
```

2. **Network Security:**
- Bind to localhost only: `--host 127.0.0.1`
- Use VPN or private networks
- Configure Azure Cosmos DB firewall rules

3. **Secrets Management:**
- Use Azure Key Vault
- Never commit `.env` to git
- Rotate keys regularly
- Use read-only keys when possible

4. **Authentication:**
- Add authentication layer to Streamlit
- Use Azure AD for SSO
- Implement rate limiting

### 🔧 Development

- Add `.env` to `.gitignore`
- Use Azure Cosmos DB Emulator for local testing
- Create separate dev/prod environments
- Use minimum required permissions

## Performance Optimization

### Query Optimization

1. **Use partition keys:**
```sql
-- Good (uses partition key)
SELECT * FROM c WHERE c.userId = '123'

-- Avoid (cross-partition)
SELECT * FROM c WHERE c.email = 'user@example.com'
```

2. **Limit results:**
```sql
-- Always use TOP
SELECT TOP 100 * FROM c WHERE c.status = 'Active'
```

3. **Index usage:**
- Check indexing policy with `get_indexing_policy`
- Use indexed fields in WHERE clauses

### Agent Optimization

1. **Reduce iterations:**
```python
cfg = Settings(max_iterations=3)  # Faster, less thorough
```

2. **Disable intermediate steps:**
```python
# In Streamlit UI
show_intermediate = False
```

3. **Cache schema:**
```python
# Schema is cached in session state
# Use "Get Schema" quick action once
```

## Contributing

We welcome contributions! 🎉

### Development Setup

```bash
# Fork and clone
git clone https://github.com/yourusername/cosmos-mcp-assistant.git
cd cosmos-mcp-assistant

# Create branch
git checkout -b feature/your-feature

# Install dev dependencies
pip install -r requirements-dev.txt

# Make changes and test
python -m pytest tests/

# Submit PR
git push origin feature/your-feature
```

### Contribution Ideas

- 🔄 Additional MCP tools (bulk operations, aggregations)
- 📊 Data visualization in Streamlit (charts, graphs)
- 🔐 Authentication layer (Azure AD, OAuth)
- 🚀 Performance monitoring dashboard
- 🌐 Multi-container support
- 📝 Query templates library
- 🎨 Custom Streamlit themes
- 🧪 Comprehensive test suite

## Project Structure

```
Streamable_HTTP/
├── server.py      # MCP server (HTTP transport)
├── client.py           # Intelligent ReAct client
├── streamlit_app.py           # Web UI
├── requirements.txt           # Python dependencies
```

## Requirements

```txt
# Azure SDK
azure-cosmos>=4.5.0
azure-identity>=1.15.0

# FastMCP
fastmcp>=0.2.0

# LangChain
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-mcp-adapters>=0.1.0
langchainhub>=0.1.14

# Streamlit
streamlit>=1.30.0
pandas>=2.0.0

# Utilities
python-dotenv>=1.0.0
```

## License

MIT License - see LICENSE file for details

## Acknowledgments

- 🙏 Anthropic for the MCP protocol
- 🙏 Azure Cosmos DB team for the Python SDK
- 🙏 LangChain community for ReAct agent framework
- 🙏 Streamlit for the beautiful UI framework
- 🙏 All contributors and early adopters

## Support

- 📚 [Azure Cosmos DB Documentation](https://docs.microsoft.com/azure/cosmos-db/)
- 📚 [MCP Protocol Specification](https://modelcontextprotocol.io/)
- 📚 [LangChain Documentation](https://python.langchain.com/)
- 📚 [Streamlit Documentation](https://docs.streamlit.io/)
- 🐛 [Report Issues](https://github.com/yourusername/cosmos-mcp-assistant/issues)

## FAQ

**Q: Do I need all three components?**  
A: No! Use just the MCP server for LLM integration, or add the client/UI as needed.

**Q: Can I use other LLM providers?**  
A: Yes! The client works with any OpenAI-compatible API. Modify `azure_endpoint` accordingly.

**Q: Does this work with Azure Cosmos DB for MongoDB/Cassandra/Gremlin?**  
A: Currently supports SQL API only. Other APIs coming soon!

**Q: Can I deploy this in production?**  
A: Yes! Use Managed Identity, proper network security, and consider adding authentication.

**Q: How much does this cost?**  
A: Costs include Azure Cosmos DB RU consumption + Azure OpenAI API calls. Start small!

---

**🚀 Ready to explore your data?**

1. Configure `.env` file
2. Start server: `python server.py`
3. Start UI: `streamlit run streamlit_app.py`
4. Open browser: `http://localhost:8501`
5. Ask: *"What's in my database?"*

**Happy querying! 🎉**

---

**Built with ❤️ for the Azure Cosmos DB community**

**Contact**: Mohammed Aftab (https://github.com/Aftabbs)