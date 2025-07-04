# Azure Cosmos DB MCP Server 

**The first Python-based MCP (Model Context Protocol) server for Azure Cosmos DB** - enabling Claude Desktop to interact directly with your Cosmos DB databases through natural language.

## What is this? 

This project allows Claude Desktop (Anthropic's AI assistant) to:
- Query your Cosmos DB databases using SQL-like syntax
- Explore data schemas and relationships
- Analyze your data patterns
- Help you understand your database structure

Think of it as giving Claude "hands" to touch and explore your Cosmos DB data while you chat with it!

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Available Tools](#available-tools)
- [Troubleshooting](#troubleshooting)
- [Common Issues & Fixes](#common-issues--fixes)
- [How It Works](#how-it-works)
- [Contributing](#contributing)

## Prerequisites

Before you begin, ensure you have:
- ✅ Windows 10/11 (for this guide, though it works on other OS too)
- ✅ [Claude Desktop](https://claude.ai/download) installed
- ✅ Azure Cosmos DB account with:
  - Account URI
  - Access Key
  - Database name
  - Container name
- ✅ Python 3.8 or higher (optional, as we'll use `uv`)

## Installation

### Step 1: Install UV (Python Package Manager)

UV is a modern, fast Python package manager that makes setup easier than pip.

Open PowerShell as Administrator and run:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2: Set Up Your Project

1. Create a new folder for your project:
```bash
mkdir cosmos-mcp-server
cd cosmos-mcp-server
```

2. Open the folder in VS Code:
```bash
code .
```

3. Initialize the project with UV:
```bash
uv init .
```

4. Add the MCP package:
```bash
uv add "mcp[cli]"
```

### Step 3: Create the Server File

Copy the `cosmos_server.py` file from this repository into your project folder.

### Step 4: Configure Claude Desktop

Run this command to set up the MCP server in Claude:
```bash
uv run mcp install cosmos_server.py
```

This creates/updates the `claude_desktop_config.json` file.

## Configuration

### Understanding claude_desktop_config.json

The configuration file tells Claude Desktop how to start your MCP server. It looks like this:

```json
{
  "mcpServers": {
    "cosmos": {
      "command": "C:\\path\\to\\your\\python.exe",
      "args": [
        "C:\\path\\to\\your\\cosmos_server.py",
        "--uri", "your-cosmos-uri",
        "--key", "your-cosmos-key",
        "--db", "your-database-name",
        "--container", "your-container-name"
      ]
    }
  }
}
```

### Configuration Methods

#### Method 1: Using Command Line Arguments (Recommended for Testing)

Edit your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "cosmos": {
      "command": "python",
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

#### Method 2: Using Environment Variables (Recommended for Production)

1. Create a `.env` file in your project (never commit this!):
```env
COSMOS_URI=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-primary-key
COSMOS_DATABASE=your-database
COSMOS_CONTAINER=your-container
```

2. Update `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "cosmos": {
      "command": "python",
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

### Finding Your Configuration File

The `claude_desktop_config.json` file is located at:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

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

###  Common Issues & Fixes

#### 1. "MCP Server Not Showing in Claude"
**Solution**: 
- Completely close Claude Desktop (check Task Manager)
- Make sure your `claude_desktop_config.json` is valid JSON
- Restart Claude Desktop

#### 2. "Changes to Tools Not Reflected"
**Solution**: Always restart Claude Desktop after updating `cosmos_server.py`:
1. Open Task Manager (Ctrl+Shift+Esc)
2. Find "Claude" or "Claude Desktop"
3. Click "End Task"
4. Start Claude Desktop again

#### 3. "Connection Failed" Errors
**Check**:
- ✅ Cosmos URI includes `https://` and port `:443/`
- ✅ Access key is correct (get from Azure Portal)
- ✅ Database and container names are exact (case-sensitive!)
- ✅ Your IP is whitelisted in Cosmos DB firewall settings

#### 4. "Module Not Found" Errors
**Solution**:
```bash
# Make sure you're in the project directory
uv add azure-cosmos
uv sync
```

#### 5. "Invalid JSON" in Config File
**Common mistakes**:
- Missing commas between fields
- Using single quotes instead of double quotes
- Trailing commas after the last item
- Backslashes in paths not escaped (use `\\` or `/`)

###  Debug Mode

To see detailed logs:

1. Run Claude Desktop from terminal:
```bash
# Windows
"C:\Program Files\Claude\Claude.exe" --enable-logging

# macOS
/Applications/Claude.app/Contents/MacOS/Claude --enable-logging
```

2. Check logs in:
- Windows: `%APPDATA%\Claude\logs\`
- macOS: `~/Library/Logs/Claude/`

## How It Works

### Architecture Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Claude Desktop │────▶│  MCP Protocol    │────▶│  Cosmos Server  │
│   (MCP Client)  │◀────│  (JSON-RPC)      │◀────│  (Python MCP)   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                                                           ▼
                                                  ┌─────────────────┐
                                                  │  Azure Cosmos   │
                                                  │     Database    │
                                                  └─────────────────┘
```

### What Happens When You Chat:

1. **You ask Claude** a question about your database
2. **Claude recognizes** it needs to use the Cosmos tools
3. **MCP Protocol** sends the request to your Python server
4. **Python server** connects to Cosmos DB and runs the operation
5. **Results flow back** through MCP to Claude
6. **Claude formats** the response in a human-friendly way

## Best Practices

###  Security
- **Never** commit your access keys to Git
- Use environment variables for sensitive data
- Consider using Azure Managed Identity when possible
- Regularly rotate your access keys

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

We welcome contributions! This is the first Python-based Cosmos DB MCP server, and there's room for improvement.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Ideas for Contributions

- 🔍 Add support for more Cosmos DB operations
- 📊 Implement data visualization tools
- 🔒 Add authentication options
- 📝 Improve error messages
- 🌍 Add support for multiple containers
- ⚡ Performance optimizations

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Thanks to Anthropic for creating the MCP protocol
- Thanks to the Azure Cosmos DB team for their excellent Python SDK
- Special thanks to early adopters and contributors

---

**Need Help?** 
- 📖 [MCP Documentation](https://docs.mcp.io)
- 📚 [Azure Cosmos DB Docs](https://docs.microsoft.com/azure/cosmos-db/)
- 💬 Open an issue in this repository

**Happy querying! 🎉**