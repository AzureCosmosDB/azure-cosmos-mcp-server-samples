package com.example.mcp;

import com.azure.cosmos.*;
import com.azure.cosmos.models.*;
import com.azure.identity.DefaultAzureCredentialBuilder;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.modelcontextprotocol.server.McpServer;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.server.McpSyncServer;
import io.modelcontextprotocol.server.transport.StdioServerTransportProvider;
import io.modelcontextprotocol.spec.McpSchema;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;

public class CosmosDBMcpServer {
    private static final Logger logger = LoggerFactory.getLogger(CosmosDBMcpServer.class);

    public static void main(String[] args) {
        ObjectMapper mapper = new ObjectMapper();
        var transport = new StdioServerTransportProvider(mapper);

        var capabilities = McpSchema.ServerCapabilities.builder()
                .resources(false, true)
                .tools(true)
                .logging()
                .build();

        McpSyncServer server = McpServer.sync(transport)
                .serverInfo("cosmosdb-mcp-server", "1.0.0")
                .capabilities(capabilities)
                .build();

        String endpoint = System.getenv("COSMOSDB_URI");
        String key = System.getenv("COSMOSDB_KEY");
        String databaseId = System.getenv("COSMOS_DATABASE_ID");

        CosmosClientBuilder clientBuilder = new CosmosClientBuilder()
                .endpoint(endpoint)
                .consistencyLevel(ConsistencyLevel.EVENTUAL);

        if (key != null && !key.isBlank()) {
            clientBuilder.key(key);
            logger.info("Using key-based Cosmos DB authentication.");
        } else {
            clientBuilder.credential(new DefaultAzureCredentialBuilder().build());
            logger.info("Using DefaultAzureCredential for Cosmos DB authentication.");
        }

        CosmosAsyncClient client = clientBuilder.buildAsyncClient();

        // Shutdown hook to close the client
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            logger.info("Shutting down Cosmos client...");
            client.close();
        }));

        var getItemTool = new McpServerFeatures.SyncToolSpecification(
                new McpSchema.Tool("get_item", "Retrieves an item from a Cosmos DB container by ID",
                        "{\"type\": \"object\", \"properties\": {\"containerName\": {\"type\": \"string\"}, \"id\": {\"type\": \"string\"}}, \"required\": [\"containerName\", \"id\"]}"),
                (exchange, argsMap) -> {
                    try {
                        String containerName = (String) argsMap.get("containerName");
                        String id = (String) argsMap.get("id");
                        CosmosAsyncContainer container = client.getDatabase(databaseId).getContainer(containerName);
                        CosmosItemResponse<Object> response = container.readItem(id, new PartitionKey(id), Object.class).block();
                        return new McpSchema.CallToolResult(response.getItem().toString(), false);
                    } catch (Exception e) {
                        logger.warn("Error in get_item: {}", e.getMessage());
                        return new McpSchema.CallToolResult("Error: " + e.getMessage(), true);
                    }
                });

        var putItemTool = new McpServerFeatures.SyncToolSpecification(
                new McpSchema.Tool("put_item", "Inserts or replaces an item in a Cosmos DB container",
                        "{\"type\": \"object\", \"properties\": {\"containerName\": {\"type\": \"string\"}, \"item\": {\"type\": \"object\"}}, \"required\": [\"containerName\", \"item\"]}"),
                (exchange, argsMap) -> {
                    try {
                        String containerName = (String) argsMap.get("containerName");
                        Map<String, Object> item = (Map<String, Object>) argsMap.get("item");
                        CosmosAsyncContainer container = client.getDatabase(databaseId).getContainer(containerName);
                        container.upsertItem(item).block();
                        return new McpSchema.CallToolResult("Item upserted", false);
                    } catch (Exception e) {
                        logger.warn("Error in put_item: {}", e.getMessage());
                        return new McpSchema.CallToolResult("Error: " + e.getMessage(), true);
                    }
                });

        var updateItemTool = new McpServerFeatures.SyncToolSpecification(
                new McpSchema.Tool("update_item", "Updates fields in an existing Cosmos DB item",
                        "{\"type\": \"object\", \"properties\": {\"containerName\": {\"type\": \"string\"}, \"id\": {\"type\": \"string\"}, \"updates\": {\"type\": \"object\"}}, \"required\": [\"containerName\", \"id\", \"updates\"]}"),
                (exchange, argsMap) -> {
                    try {
                        String containerName = (String) argsMap.get("containerName");
                        String id = (String) argsMap.get("id");
                        Map<String, Object> updates = (Map<String, Object>) argsMap.get("updates");
                        CosmosAsyncContainer container = client.getDatabase(databaseId).getContainer(containerName);
                        CosmosItemResponse<Object> response = container.readItem(id, new PartitionKey(id), Object.class).block();
                        Map<String, Object> current = (Map<String, Object>) response.getItem();
                        current.putAll(updates);
                        container.replaceItem(current, id, new PartitionKey(id)).block();
                        return new McpSchema.CallToolResult("Item updated", false);
                    } catch (Exception e) {
                        logger.warn("Error in update_item: {}", e.getMessage());
                        return new McpSchema.CallToolResult("Error: " + e.getMessage(), true);
                    }
                });

        var queryContainerTool = new McpServerFeatures.SyncToolSpecification(
                new McpSchema.Tool("query_container", "Runs a SQL query against a Cosmos DB container",
                        "{\"type\": \"object\", \"properties\": {\"containerName\": {\"type\": \"string\"}, \"query\": {\"type\": \"string\"}}, \"required\": [\"containerName\", \"query\"]}"),
                (exchange, argsMap) -> {
                    try {
                        logger.info("Received query_container request with args: {}", argsMap);
                        String containerName = (String) argsMap.get("containerName");
                        String query = (String) argsMap.get("query");
                        CosmosAsyncContainer container = client.getDatabase(databaseId).getContainer(containerName);

                        CosmosQueryRequestOptions options = new CosmosQueryRequestOptions();
                        StringBuilder resultBuilder = new StringBuilder("[");
                        container.queryItems(query, options, Object.class).toIterable().forEach(item -> {
                            if (resultBuilder.length() > 1) resultBuilder.append(",");
                            resultBuilder.append(item.toString());
                        });
                        resultBuilder.append("]");
                        return new McpSchema.CallToolResult(resultBuilder.toString(), false);
                    } catch (Exception e) {
                        logger.warn("Error in query_container: {}", e.getMessage());
                        return new McpSchema.CallToolResult("Error: " + e.getMessage(), true);
                    }
                });

        server.addTool(getItemTool);
        server.addTool(putItemTool);
        server.addTool(updateItemTool);
        server.addTool(queryContainerTool);

        logger.info("CosmosDB MCP server running...");
    }
}
