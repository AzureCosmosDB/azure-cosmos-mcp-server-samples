# Azure Cosmos DB MCP Server 

**The first Python-based MCP (Model Context Protocol) server for Azure Cosmos DB** - enabling Claude Desktop and other LLMs to interact directly with your Azure Cosmos DB databases through natural language.

## What is this? 

This project allows AI assistants (Claude, Continue.dev, etc.) to:
- Query your Azure Cosmos DB databases using SQL-like syntax
- Explore data schemas and relationships
- Analyze your data patterns
- Help you understand your database structure

Think of it as giving AI "hands" to touch and explore your Azure Cosmos DB data while you chat with it!

## ✨ What's New in v0.2.0

- 🚀 **Streamable HTTP Transport**: Modern, scalable transport protocol
- 🔧 **FastMCP 2.3.0**: Upgraded to latest FastMCP version
- 📦 **Simplified Setup**: No transport configuration needed - just run!
- 🌐 **Multiple LLM Support**: Works with Claude Desktop, Continue.dev, and more
- 📋 **Transport Bridge**: Easy Claude Desktop integration via proxy
- 🔄 **Environment Variables**: Automatic `.env` file loading with python-dotenv

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Transport Configuration](#transport-configuration)
- [LLM Integration](#llm-integration)
- [Available Tools](#available-tools)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)
- [Contributing](#contributing)

## Prerequisites

Before you begin, ensure you have:
- ✅ Windows, macOS, or Linux
- ✅ Python 3.8 or higher
- ✅ Azure Cosmos DB account with:
  - Account URI
  - Access Key
  - Database name
  - Container name
- ✅ One of these LLM clients:
  - [Claude Desktop](https://claude.ai/download)
  - [Continue.dev](https://continue.dev/)
  - Any MCP-compatible client

## Installation

### Quick Setup

1. **Clone the repository:**
```bash
git clone https://github.com/AzureCosmosDB/azure-cosmos-mcp-server-samples.git
cd azure-cosmos-mcp-server-samples/python
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

# Verify FastMCP version (should be 2.3.0+)
pip show fastmcp
```

4. **Create environment configuration:**
```bash
# Create .env file
echo "COSMOS_URI=https://your-account.documents.azure.com:443/" > .env
echo "COSMOS_KEY=your-primary-key" >> .env
echo "COSMOS_DATABASE=your-database" >> .env
echo "COSMOS_CONTAINER=your-container" >> .env
```

5. **Start the server:**
```bash
# Simple start (uses environment variables from .env)
python cosmos_server.py
```

> **Note:** The server will automatically:
> - Use Streamable HTTP transport on `127.0.0.1:8080` 
> - Load configuration from `.env` file or environment variables
> - No additional arguments needed!

Your server will be running at `http://127.0.0.1:8080/mcp/` 🚀

## Transport Configuration

### Streamable HTTP (Default)

**Best for**: Production deployments, web-based integrations, Continue.dev, multiple LLM clients

```bash
# Default start (recommended for most users)
python cosmos_server.py
```

> **Note:** The server runs on `127.0.0.1:8080` by default and loads configuration from your `.env` file.

### Host Configuration Guide

The server runs on `127.0.0.1:8080` by default with Streamable HTTP transport. This provides the best balance of security and functionality for most use cases.

## LLM Integration

### 🎯 Continue.dev (Recommended - Direct HTTP)

Continue.dev natively supports Streamable HTTP transport, making integration seamless:

**1. Add to your Continue.dev config:**

```yaml
name: Azure Cosmos DB MCP server
version: 0.2.0
schema: v1
mcpServers:
  - name: Azure Cosmos DB Explorer
    type: streamable-http
    url: http://127.0.0.1:8080/mcp/
```

**2. Start the server:**
```bash
python cosmos_server.py
```

**3. Use in Continue.dev:**
```
@Azure Cosmos DB Explorer what containers do I have in my database?
```

### 🔄 Claude Desktop (via Transport Bridge)

Since Claude Desktop uses STDIO, we need a transport bridge to connect to our HTTP server:

**1. Create `proxy.py` (Transport Bridge):**

```python
# proxy.py - Transport Bridging for Claude Desktop
# Link: https://gofastmcp.com/servers/proxy#transport-bridging

from fastmcp import FastMCP

mcp = FastMCP.as_proxy("http://127.0.0.1:8080/mcp/", name="Azure Cosmos DB Explorer")

if __name__ == "__main__":
    mcp.run()
```

**2. Claude Desktop Configuration:**

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cosmos": {
      "command": "python",
      "args": [
        "path/to/proxy.py"
      ],
      "env": {},
      "transport": "stdio"
    }
  }
}
```

**3. Start both servers:**

```bash
# Terminal 1: Start the main MCP server
python cosmos_server.py

# Terminal 2: Claude Desktop will automatically start the proxy
# Just restart Claude Desktop
```

### 🔧 Alternative: UV Package Manager

If you prefer using `uv`:

```json
{
  "mcpServers": {
    "cosmos": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "path/to/proxy.py"
      ],
      "env": {},
      "transport": "stdio"
    }
  }
}
```

### 🎨 Other LLM Clients

Any MCP-compatible client can connect to the HTTP endpoint:

**Endpoint**: `http://127.0.0.1:8080/mcp/`  
**Protocol**: JSON-RPC over HTTP  
**Content-Type**: `application/json`

## Available Tools

Your MCP server provides these tools to any connected LLM:

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

## Environment Variables

Create a `.env` file or set environment variables:

```env
COSMOS_URI=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-primary-key
COSMOS_DATABASE=your-database
COSMOS_CONTAINER=your-container
```

## Command Line Options

```bash
python cosmos_server.py [OPTIONS]

Options:
  --uri TEXT                 Cosmos DB URI
  --key TEXT                 Cosmos DB Key  
  --db TEXT                  Database name
  --container TEXT           Container name
  --use-managed-identity     Use Azure Managed Identity
  --version                  Show version
  --help                     Show help message
```

> **Note:** All options can be set via environment variables in your `.env` file instead of command line arguments.

## Security Best Practices

### 🔒 Production Environments

**Azure Managed Identity (Recommended for production):**

```bash
# Enable managed identity and skip access keys
python cosmos_server.py --use-managed-identity
```

**Network Security:**
- Use `--host 127.0.0.1` for local-only access
- Use `--host 0.0.0.0` only with proper firewall rules
- Consider VPN or private networks for production

### 🔧 Development Environments

- Never commit `.env` files to version control
- Add `.env` to `.gitignore`
- Use read-only keys when possible
- Consider Azure Cosmos DB Emulator for local development

## Troubleshooting

### Common Issues

**1. Server won't start**
```bash
# Check if port is already in use 
netstat -an | grep 8080

# Configure different port in 
 cosmos_server.py 
```

**2. Continue.dev can't connect**
- Ensure server is running: `curl http://127.0.0.1:8080/mcp/`
- Check Continue.dev logs for connection errors
- Verify URL in Continue.dev config

**3. Claude Desktop proxy issues**
- Restart both the server and Claude Desktop
- Check proxy.py file permissions
- Verify paths in claude_desktop_config.json

**4. Connection refused**
- Verify Azure Cosmos DB credentials
- Check firewall settings
- Ensure database and container exist


## Performance Tips

- Use partition keys in queries for better performance
- Start with small queries on large containers
- Limit sample document requests (default: 5, max: 100)
- Use `COUNT` queries to check container sizes first

## Contributing

We welcome contributions! 

### Development Setup

```bash
git clone https://github.com/AzureCosmosDB/azure-cosmos-mcp-server-samples.git
cd azure-cosmos-mcp-server-samples/python

# Create feature branch
git checkout -b feature/your-feature

# Make changes and test
python cosmos_server.py --transport streamable-http

# Submit PR
git push origin feature/your-feature
```

### Ideas for Contributions

- 🔄 Additional Azure Cosmos DB operations
- 📊 Data visualization tools  
- 🔐 Enhanced authentication options
- 🚀 Performance optimizations
- 📝 Better error messages
- 🌐 Multi-container support

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   LLM Clients   │────▶│  HTTP Transport  │────▶│  FastMCP Server │
│ (Continue.dev,  │◀────│  (Port 8080)     │◀────│   (Python)      │
│  Claude+Proxy)  │     └──────────────────┘     └────────┬────────┘
└─────────────────┘                                       │
                                                           ▼
                                                  ┌─────────────────┐
                                                  │  Azure Cosmos   │
                                                  │     Database    │
                                                  └─────────────────┘
```

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Thanks to Anthropic for the MCP protocol
- Thanks to Azure Cosmos DB team for the Python SDK
- Thanks to Continue.dev for native MCP support
- Special thanks to contributors and early adopters

---

**🚀 Ready to explore your data?**

1. Start server: `python cosmos_server.py`
2. Configure your LLM client
3. Ask: *"What containers do I have in my database?"*

**Need Help?** 
- 🌐 [Azure Cosmos DB Docs](https://docs.microsoft.com/azure/cosmos-db/)
- 💬 [Continue.dev Docs](https://continue.dev/docs)
- 🐛 [Open an issue](https://github.com/AzureCosmosDB/azure-cosmos-mcp-server-samples/issues)

**Happy querying! 🎉**