#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { CosmosClient } from "@azure/cosmos";
import * as dotenv from "dotenv";
dotenv.config();


// Cosmos DB client initialization
const cosmosClient = new CosmosClient({
  endpoint: process.env.COSMOSDB_URI!,
  key: process.env.COSMOSDB_KEY!,
});

// Get DB and container config from env vars
const databaseId = process.env.COSMOS_DATABASE_ID!;
const containerId = process.env.COSMOS_CONTAINER_ID!;

const container = cosmosClient.database(databaseId).container(containerId);

// Tool definitions
const UPDATE_ITEM_TOOL: Tool = {
  name: "update_item",
  description: "Updates specific attributes of an item in a Azure Cosmos DB container",
  inputSchema: {
    type: "object",
    properties: {
      containerName: { type: "string", description: "Name of the container" },
      id: { type: "string", description: "ID of the item to update" },
      updates: { type: "object", description: "The updated attributes of the item" },
    },
    required: ["containerName", "id", "updates"],
  },
};

const PUT_ITEM_TOOL: Tool = {
  name: "put_item",
  description: "Inserts or replaces an item in a Azure Cosmos DB container",
  inputSchema: {
    type: "object",
    properties: {
      containerName: { type: "string", description: "Name of the  container" },
      item: { type: "object", description: "Item to insert into the container" },
    },
    required: ["containerName", "item"],
  },
};

const GET_ITEM_TOOL: Tool = {
  name: "get_item",
  description: "Retrieves an item from a Azure Cosmos DB container by its ID",
  inputSchema: {
    type: "object",
    properties: {
      containerName: { type: "string", description: "Name of the container" },
      id: { type: "string", description: "ID of the item to retrieve" },
    },
    required: ["containerName", "id"],
  },
};

const QUERY_CONTAINER_TOOL: Tool = {
  name: "query_container",
  description: "Queries an Azure Cosmos DB container using SQL-like syntax",
  inputSchema: {
    type: "object",
    properties: {
      containerName: { type: "string", description: "Name of the container" },
      query: { type: "string", description: "SQL query string" },
      parameters: { 
        type: "array", 
        description: "Query parameters",
        items: {
          type: "object",
          properties: {
            name: { type: "string", description: "Parameter name" },
            value: { type: "string", description: "Parameter value" } // Adjust type as needed
          },
          required: ["name", "value"]
        }
      },
    },
    required: ["containerName", "query", "parameters"],
  },
};

async function updateItem(params: any) {
  try {
    const { id, updates } = params;
    const { resource } = await container.item(id).read();
    
    if (!resource) {
      throw new Error("Item not found");
    }

    const updatedItem = { ...resource, ...updates };

    const { resource: updatedResource } = await container.item(id).replace(updatedItem);
    return {
      success: true,
      message: `Item updated successfully`,
      item: updatedResource,
    };
  } catch (error) {
    console.error("Error updating item:", error);
    return {
      success: false,
      message: `Failed to update item: ${error}`,
    };
  }
}

async function putItem(params: any) {
  try {
    const { item } = params;
    const { resource } = await container.items.create(item);

    return {
      success: true,
      message: `Item added successfully to container`,
      item: resource,
    };
  } catch (error) {
    console.error("Error putting item:", error);
    return {
      success: false,
      message: `Failed to put item: ${error}`,
    };
  }
}

async function getItem(params: any) {
  try {
    const { id } = params;
    const { resource } = await container.item(id).read();

    return {
      success: true,
      message: `Item retrieved successfully`,
      item: resource,
    };
  } catch (error) {
    console.error("Error getting item:", error);
    return {
      success: false,
      message: `Failed to get item: ${error}`,
    };
  }
}

async function queryContainer(params: any) {
  try {
    const { query, parameters } = params;
    const { resources } = await container.items.query({ query, parameters }).fetchAll();

    return {
      success: true,
      message: `Query executed successfully`,
      items: resources,
    };
  } catch (error) {
    console.error("Error querying container:", error);
    return {
      success: false,
      message: `Failed to query container: ${error}`,
    };
  }
}


const server = new Server(
  {
    name: "cosmosdb-mcp-server",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

// Request handlers
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [PUT_ITEM_TOOL, GET_ITEM_TOOL, QUERY_CONTAINER_TOOL, UPDATE_ITEM_TOOL],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result;
    switch (name) {
      case "put_item":
        result = await putItem(args);
        break;
      case "get_item":
        result = await getItem(args);
        break;
      case "query_container":
        result = await queryContainer(args);
        break;
      case "update_item":
        result = await updateItem(args);
        break;
      default:
        return {
          content: [{ type: "text", text: `Unknown tool: ${name}` }],
          isError: true,
        };
    }

    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    };
  } catch (error) {
    return {
      content: [{ type: "text", text: `Error occurred: ${error}` }],
      isError: true,
    };
  }
});

// Server startup
async function runServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Azure Cosmos DB Server running on stdio");
}

runServer().catch((error) => {
  console.error("Fatal error running server:", error);
  process.exit(1);
});
