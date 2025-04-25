package tools

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func ExecuteQuery(clientRetriever CosmosDBClientRetriever) (mcp.Tool, server.ToolHandlerFunc) {

	return execute_query(), func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {

		account, ok := request.Params.Arguments["account"].(string)
		if !ok || account == "" {
			return nil, errors.New("cosmos db account name missing")
		}
		database, ok := request.Params.Arguments["database"].(string)
		if !ok || database == "" {
			return nil, errors.New("database name missing")
		}
		container, ok := request.Params.Arguments["container"].(string)
		if !ok || container == "" {
			return nil, errors.New("container name missing")
		}
		query, ok := request.Params.Arguments["query"].(string)
		if !ok || query == "" {
			return nil, errors.New("query string missing")
		}

		partitionKeyValue, hasPartitionKey := request.Params.Arguments["partitionKey"].(string)

		client, err := clientRetriever.Get(account)

		if err != nil {
			fmt.Printf("Error creating Cosmos client: %v\n", err)
			return nil, err
		}

		databaseClient, err := client.NewDatabase(database)
		if err != nil {
			return nil, fmt.Errorf("error creating database client: %v", err)
		}

		containerClient, err := databaseClient.NewContainer(container)
		if err != nil {
			return nil, fmt.Errorf("error creating container client: %v", err)
		}

		var partitionKey azcosmos.PartitionKey
		if hasPartitionKey {
			partitionKey = azcosmos.NewPartitionKeyString(partitionKeyValue)
		} else {
			partitionKey = azcosmos.PartitionKey{} // Empty partition key for cross-partition queries
		}

		queryPager := containerClient.NewQueryItemsPager(query, partitionKey, nil)

		var response ExecuteQueryResponse

		for queryPager.More() {
			queryResponse, err := queryPager.NextPage(context.Background())
			if err != nil {
				return nil, fmt.Errorf("query page error: %v", err)
			}

			// Store items directly as json.RawMessage
			for _, item := range queryResponse.Items {
				response.QueryResults = append(response.QueryResults, json.RawMessage(item))
			}

			response.QueryMetrics = append(response.QueryMetrics, *queryResponse.QueryMetrics)
		}

		// Set metrics information

		// Marshal the entire response struct
		jsonResult, err := json.Marshal(response)
		if err != nil {
			return nil, fmt.Errorf("json marshal error: %v", err)
		}

		return mcp.NewToolResultText(string(jsonResult)), nil
	}
}

type ExecuteQueryResponse struct {
	QueryResults []json.RawMessage `json:"results"`
	QueryMetrics []string          `json:"metrics"`
}

func execute_query() mcp.Tool {

	return mcp.NewTool(EXECUTE_QUERY_TOOL_NAME,
		mcp.WithString("account",
			mcp.Required(),
			mcp.Description(ACCOUNT_PARAMETER_DESCRIPTION),
		),
		mcp.WithString("database",
			mcp.Required(),
			mcp.Description("Name of the database"),
		),
		mcp.WithString("container",
			mcp.Required(),
			mcp.Description("Name of the container to query"),
		),
		mcp.WithString("query",
			mcp.Required(),
			mcp.Description("The SQL query string to execute."),
		),
		mcp.WithString("partitionKey",
			mcp.Description("The partition key value for the query. If provided, the query will be scoped to this partition."),
		),
		mcp.WithDescription("Execute a general query on a Cosmos DB container. If the query fails with an error related to cross partition query, do not ask the user to provide a partition key. Instead, try a different query that does not require a partition key. Do not use the `TOP`, `ORDER BY`, `OFFSET LIMIT`, `DISTINCT` and `GROUP BY` clauses in the query as they are not supported by the SDK used to implement this tool. Simple projections and Filters are supported in the query. Ensure that the query string is valid and adheres to Cosmos DB SQL syntax. To use a partition key in the query directly, add it in the WHERE clause. Example: SELECT * FROM c WHERE c.department='HR'."),
	)
}

func ReadItem(clientRetriever CosmosDBClientRetriever) (mcp.Tool, server.ToolHandlerFunc) {

	return readItem(), func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {

		account, ok := request.Params.Arguments["account"].(string)
		if !ok || account == "" {
			return nil, errors.New("cosmos db account name missing")
		}
		database, ok := request.Params.Arguments["database"].(string)
		if !ok || database == "" {
			return nil, errors.New("database name missing")
		}
		container, ok := request.Params.Arguments["container"].(string)
		if !ok || container == "" {
			return nil, errors.New("container name missing")
		}
		itemID, ok := request.Params.Arguments["itemID"].(string)
		if !ok || itemID == "" {
			return nil, errors.New("item ID missing")
		}
		partitionKeyValue, ok := request.Params.Arguments["partitionKey"].(string)
		if !ok || partitionKeyValue == "" {
			return nil, errors.New("partition key missing")
		}

		client, err := clientRetriever.Get(account)

		if err != nil {
			fmt.Printf("Error creating Cosmos client: %v\n", err)
			return nil, err
		}

		databaseClient, err := client.NewDatabase(database)
		if err != nil {
			return nil, fmt.Errorf("error creating database client: %v", err)
		}

		containerClient, err := databaseClient.NewContainer(container)
		if err != nil {
			return nil, fmt.Errorf("error creating container client: %v", err)
		}

		partitionKey := azcosmos.NewPartitionKeyString(partitionKeyValue)
		itemResponse, err := containerClient.ReadItem(ctx, partitionKey, itemID, nil)
		if err != nil {
			return nil, fmt.Errorf("error reading item: %v", err)
		}

		// var item map[string]interface{}
		// if err := json.Unmarshal(itemResponse.Value, &item); err != nil {
		// 	return nil, fmt.Errorf("error unmarshalling item: %v", err)
		// }

		// jsonResult, err := json.Marshal(item)
		// if err != nil {
		// 	return nil, fmt.Errorf("error marshalling item to JSON: %v", err)
		// }

		return mcp.NewToolResultText(string(itemResponse.Value)), nil
	}
}

func readItem() mcp.Tool {

	return mcp.NewTool(READ_ITEM_TOOL_NAME,
		mcp.WithString("account",
			mcp.Required(),
			mcp.Description(ACCOUNT_PARAMETER_DESCRIPTION),
		),
		mcp.WithString("database",
			mcp.Required(),
			mcp.Description("Name of the database"),
		),
		mcp.WithString("container",
			mcp.Required(),
			mcp.Description("Name of the container to read data from"),
		),
		mcp.WithString("itemID",
			mcp.Required(),
			mcp.Description("ID of the item to read"),
		),
		mcp.WithString("partitionKey",
			mcp.Required(),
			mcp.Description("Partition key of the item"),
		),
		mcp.WithDescription("Read a specific item from a container in a Cosmos DB database"),
	)
}
