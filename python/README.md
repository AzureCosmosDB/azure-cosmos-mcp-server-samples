# Azure Cosmos DB MCP Server 

**The first Python-based MCP (Model Context Protocol) server for Azure Cosmos DB** - enabling Claude Desktop to interact directly with your Azure Cosmos DB databases through natural language.

## What is this? 

This project allows Claude Desktop (Anthropic's AI assistant) to:
- Query your Azure Cosmos DB databases using SQL-like syntax
- Explore data schemas and relationships
- Analyze your data patterns
- Help you understand your database structure

Think of it as giving Claude "hands" to touch and explore your Azure Cosmos DB data while you chat with it!

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Available Tools](#available-tools)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)
- [Common Issues & Fixes](#common-issues--fixes)
- [How It Works](#how-it-works)
- [Contributing](#contributing)

## Prerequisites

Before you begin, ensure you have:
- ✅ Windows, macOS, or Linux
- ✅ [Claude Desktop](https://claude.ai/download) installed
- ✅ Azure Cosmos DB account with:
  - Account URI
  - Access Key
  - Database name
  - Container name
- ✅ Python 3.8 or higher

## Installation

You can install using either `pip` (traditional) or `uv` (modern). Choose the method you're most comfortable with.

### Option 1: Using pip (Traditional Method)

1. Clone the repository:
```bash
git clone https://github.com/AzureCosmosDB/azure-cosmos-mcp-server-samples.git
cd azure-cosmos-mcp-server-samples/cosmos-python
```

2. Create a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install MCP CLI tools:
```bash
pip install mcp[cli]
```

5. Configure Claude Desktop (make sure your virtual environment is activated):
```bash
# If the command isn't found, ensure your virtual environment is activated
mcp install cosmos_server.py
```

### Option 2: Using uv (Modern Method)

UV is a modern, fast Python package manager that simplifies dependency management.

1. Install UV:
```bash
# Windows PowerShell (as Administrator)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone and setup:
```bash
git clone https://github.com/AzureCosmosDB/azure-cosmos-mcp-server-samples.git
cd azure-cosmos-mcp-server-samples/cosmos-python
```

3. Initialize and install:
```bash
uv init .
uv add "mcp[cli]"
uv add azure-cosmos
```

4. Configure Claude Desktop:
```bash
uv run mcp install cosmos_server.py
```

### Generating requirements.txt

If you need to generate a fresh `requirements.txt`:

**Using pip:**
```bash
pip freeze > requirements.txt
```

**Using uv:**
```bash
uv pip compile pyproject.toml -o requirements.txt
```

## Configuration

### Understanding claude_desktop_config.json

The configuration file tells Claude Desktop how to start your MCP server. It's located at:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Configuration Methods

#### Method 1: Using Command Line Arguments

Edit your `claude_desktop_config.json`:

**Windows paths:**
```json
{
  "mcpServers": {
    "cosmos": {
      "command": "C:\\path\\to\\python.exe",
      "args": [
        "C:\\path\\to\\cosmos_server.py",
        "--uri", "https://your-account.documents.azure.com:443/",
        "--key", "your-primary-key",
        "--db", "your-database",
        "--container", "your-container"
      ]
    }
  }
}
```

**Unix/macOS/Linux paths:**
```json
{
  "mcpServers": {
    "cosmos": {
      "command": "/usr/bin/python3",
      "args": [
        "/home/username/cosmos-mcp/cosmos_server.py",
        "--uri", "https://your-account.documents.azure.com:443/",
        "--key", "your-primary-key",
        "--db", "your-database",
        "--container", "your-container"
      ]
    }
  }
}
```

#### Method 2: Using Environment Variables (Recommended)

1. Create a `.env` file in your project:
```env
COSMOS_URI=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-primary-key
COSMOS_DATABASE=your-database
COSMOS_CONTAINER=your-container
```

**Note:** Environment variables are loaded automatically by the MCP server. You don't need to install `python-dotenv` as the server reads from system environment variables directly.

2. Update `claude_desktop_config.json`:

**Windows:**
```json
{
  "mcpServers": {
    "cosmos": {
      "command": "C:\\path\\to\\python.exe",
      "args": ["C:\\path\\to\\cosmos_server.py"],
      "env": {
        "COSMOS_URI": "https://your-account.documents.azure.com:443/",
        "COSMOS_KEY": "your-primary-key",
        "COSMOS_DATABASE": "your-database",
        "COSMOS_CONTAINER": "your-container"
      }
    }
  }
}
```

**Unix/macOS/Linux:**
```json
{
  "mcpServers": {
    "cosmos": {
      "command": "/usr/bin/python3",
      "args": ["/home/username/cosmos-mcp/cosmos_server.py"],
      "env": {
        "COSMOS_URI": "https://your-account.documents.azure.com:443/",
        "COSMOS_KEY": "your-primary-key",
        "COSMOS_DATABASE": "your-database",
        "COSMOS_CONTAINER": "your-container"
      }
    }
  }
}
```

## Security Best Practices

###  Production Environments

For production use, we strongly recommend using **Azure Managed Identity** instead of access keys:

#### Using Azure Managed Identity (Recommended)

1. **Enable Managed Identity** on your Azure resource (VM, App Service, etc.)

2. **Grant Cosmos DB access** to the Managed Identity:
```bash
# Using Azure CLI
az cosmosdb sql role assignment create \
  --account-name "your-cosmos-account" \
  --resource-group "your-resource-group" \
  --role-definition-name "Cosmos DB Built-in Data Reader" \
  --principal-id "your-managed-identity-principal-id" \
  --scope "/dbs/your-database/colls/your-container"
```

3. **Update your code** to use DefaultAzureCredential:
```python
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

# No keys needed - uses Managed Identity automatically
credential = DefaultAzureCredential()
client = CosmosClient(url=COSMOS_URI, credential=credential)
```

#### Additional Security Recommendations

1. **Key Rotation**: If using access keys, rotate them regularly
2. **Least Privilege**: Grant minimum required permissions
3. **Network Security**: Use private endpoints and firewall rules
4. **Audit Logging**: Enable diagnostic logging in Azure Cosmos DB
5. **Secret Management**: Use Azure Key Vault for storing sensitive configuration

###  Development Environments

For development:
- Use `.env` files but **never commit them to version control**
- Add `.env` to your `.gitignore`
- Use read-only keys when possible
- Consider using the Azure Cosmos DB Emulator for local development

## Usage

### Starting the Server

1. **Save your configuration** file after making changes
2. **Restart Claude Desktop** (very important!)
3. Open Claude Desktop
4. You should see "cosmos" in the MCP servers list (look for the 🔌 icon)

### Example Conversations with Claude

Once connected, you can ask Claude things like:

```
"Can you show me what containers are in my Cosmos database?"

"What's the schema of my Users container?"

"Query the Products container and show me items where price > 100"

"How many documents are in my Orders container?"

"Show me 5 sample documents from the Customers container"

"What are the distinct values in the 'status' field?"
```

## Available Tools

Your MCP server provides these tools to Claude:

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `query_cosmos` | Run SQL queries | "SELECT * FROM c WHERE c.type = 'customer'" |
| `list_collections` | List all containers | "What containers do I have?" |
| `describe_container` | Show container schema | "What fields are in the Users container?" |
| `find_implied_links` | Find relationships | "What foreign keys might exist?" |
| `get_sample_documents` | Preview data | "Show me 3 sample documents" |
| `count_documents` | Count total documents | "How many records are there?" |
| `get_partition_key_info` | Get partition key | "What's the partition key?" |
| `get_indexing_policy` | View indexing policy | "Show me the indexing configuration" |
| `list_distinct_values` | Get unique values | "What are all the product categories?" |

## Troubleshooting

### Common Issues & Fixes

#### 1. "MCP Server Not Showing in Claude"
**Solution**: 
- Completely close Claude Desktop (check Task Manager/Activity Monitor)
- Make sure your `claude_desktop_config.json` is valid JSON
- Restart Claude Desktop

#### 2. "mcp: command not found"
**Solution**: 
- Ensure your virtual environment is activated
- For pip: `source venv/bin/activate` (Unix) or `venv\Scripts\activate` (Windows)
- For uv: Commands are run with `uv run` prefix

#### 3. "Changes to Tools Not Reflected"
**Solution**: Always restart Claude Desktop after updating `cosmos_server.py`:
- Windows: Task Manager → End Task on Claude
- macOS: Activity Monitor → Quit Claude
- Linux: `pkill -f Claude` or use System Monitor

#### 4. "Connection Failed" Errors
**Check**:
- ✅ Azure Cosmos URI includes `https://` and port `:443/`
- ✅ Access key is correct (get from Azure Portal)
- ✅ Database and container names are exact (case-sensitive!)
- ✅ Your IP is whitelisted in Azure Cosmos DB firewall settings

#### 5. "Module Not Found" Errors
**For pip users**:
```bash
# Ensure virtual environment is activated, then:
pip install -r requirements.txt
```

**For uv users**:
```bash
uv sync
```

###  Debug Mode

To see detailed logs:

**Windows:**
```bash
"C:\Program Files\Claude\Claude.exe" --enable-logging
```

**macOS:**
```bash
/Applications/Claude.app/Contents/MacOS/Claude --enable-logging
```

**Linux:**
```bash
claude --enable-logging
```

Check logs in:
- Windows: `%APPDATA%\Claude\logs\`
- macOS: `~/Library/Logs/Claude/`
- Linux: `~/.config/Claude/logs/`

## How It Works

### Architecture Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Claude Desktop │────▶│  MCP Protocol    │────▶│  Azure Cosmos Server  │
│   (MCP Client)  │◀────│  (JSON-RPC)      │◀────│  (Python MCP)   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                                                           ▼
                                                  ┌─────────────────┐
                                                  │  Azure Cosmos   │
                                                  │     Database    │
                                                  └─────────────────┘
```

## Best Practices

###  Performance
- Start with small queries when exploring large containers
- Use partition keys in queries when possible
- Limit sample document requests to reasonable numbers

###  Tips
- Ask Claude to explain query results
- Use Claude to help write complex queries
- Ask for data visualizations (Claude can create charts!)
- Request data analysis and patterns

## Contributing

We welcome contributions! This is the first Python-based Azure Cosmos DB MCP server, and there's room for improvement.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Ideas for Contributions

-  Add support for more Azure Cosmos DB operations
-  Implement data visualization tools
-  Add authentication options
-  Improve error messages
-  Add support for multiple containers
-  Performance optimizations

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Thanks to Anthropic for creating the MCP protocol
- Thanks to the Azure Cosmos DB team for their excellent Python SDK
- Special thanks to early adopters and contributors

---

**Need Help?** 
-  [MCP Documentation](https://docs.mcp.io)
-  [Azure Cosmos DB Docs](https://docs.microsoft.com/azure/cosmos-db/)
-  Open an issue in this repository

**Happy querying! **
