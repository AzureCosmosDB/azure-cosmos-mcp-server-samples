# MCP Server for Azure Cosmos DB using the Java SDK

This is an implementation of a Model Context Protocol (MCP) server for Azure Cosmos DB using the [Azure Cosmos Java SDK](https://learn.microsoft.com/en-us/java/api/overview/azure/cosmos-readme?view=azure-java-stable). It exposes a set of tools for interacting with Cosmos DB through an LLM or agent using the MCP standard.

### 🚀 Exposed Tools

- **Get Item**: Retrieve a specific item from a Cosmos DB container using its ID.
- **Put Item**: Insert or replace an item in a Cosmos DB container.
- **Update Item**: Update specific fields of an existing item in a Cosmos DB container.
- **Query Container**: Execute a SQL query against a Cosmos DB container.

> This server uses [modelcontextprotocol/mcp](https://www.npmjs.com/package/@modelcontextprotocol/sdk) via the [Java SDK](https://modelcontextprotocol.org/docs/java/sdk) and communicates using the `stdio` transport. It is intended for use in environments like [VS Code Agent Mode](https://code.visualstudio.com/docs/copilot/chat/chat-agent-mode), [Spring AI](https://docs.spring.io/spring-ai/reference/), and Claude Desktop.

---

## 🧪 Demo

Here’s how the MCP server works in a developer setup using VS Code Agent Mode (with the [vehicles.json](../dataset/vehicles.json) dataset in this repo loaded):

![Demo](./media/demo.gif)

---

## 🛠️ How to Run

Clone the repo and build:

```bash
git clone https://github.com/<your-org>/azure-cosmos-mcp-server
cd azure-cosmos-mcp-server/java
mvn clean package
```

This creates a self-contained executable JAR at:

```
target/cosmosdb-mcp-server-1.0-SNAPSHOT.jar
```

You can then launch the server like so:

```bash
java -jar target/cosmosdb-mcp-server-1.0-SNAPSHOT.jar
```

---

## ⚙️ Configure in VS Code Agent Mode

You can [follow these instructions](https://code.visualstudio.com/docs/copilot/chat/mcp-servers#_add-an-mcp-server) on how to configure this server using an `mcp.json` file.

### Sample config:

```json
{
  "servers": {
    "cosmosdb": {
      "command": "java",
      "args": ["-jar", "C:\\path\\to\\compiled\\jar\\cosmosdb-mcp-server-1.0-SNAPSHOT.jar"]
    }
  }
}

```

Once saved, restart VS Code and open the Agent Mode panel to interact with the server.

---

## 🔐 Azure Cosmos DB Authentication

This Java MCP server uses [DefaultAzureCredential](https://learn.microsoft.com/java/api/overview/azure/identity-readme?view=azure-java-stable#defaultazurecredential) for authentication. See documentation [here](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/how-to-grant-data-plane-access?tabs=built-in-definition%2Ccsharp&pivots=azure-interface-cli) for granting data plane RBAC access in Azure Cosmos DB. It expects the following environment variables:

- `COSMOSDB_URI`: your Cosmos DB account URI
- `COSMOSDB_KEY`: your Cosmos DB account key - this is optional (and not recommended) but will be used if present
- `COSMOS_DATABASE_ID`: set to the database name
- `COSMOS_CONTAINER_ID`: set this to the container name

You can also set the environment variables in your server config if you prefer, e.g.:

```json
{
  "servers": {
    "cosmosdb": {
      "command": "java",
      "args": ["-jar", "C:\\path\\to\\compiled\\jar\\cosmosdb-mcp-server-1.0-SNAPSHOT.jar"],
      "env": {
        "COSMOSDB_URI": "https://tvkmcp.documents.azure.com:443/",
        "COSMOS_DATABASE_ID": "database",
        "COSMOS_CONTAINER_ID": "Vehicles"
      }
    }
  }
}

```

> Partition keys must be embedded in your items for proper read/update behavior.

---

## 🧪 Local Dev and Testing

You can test the server with the [MCP Inspector](https://modelcontextprotocol.org/docs/tools/inspector):

```bash
npx @modelcontextprotocol/inspector java -jar ./target/cosmosdb-mcp-server-1.0-SNAPSHOT.jar
```

---

## 📝 Notes

- The server is launched as a subprocess and communicates via `stdin`/`stdout` (no network port).
- It does not yet support resources, prompts, etc. 
