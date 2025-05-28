package tools

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/Azure/azure-sdk-for-go/sdk/azcore"
	"github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func ListContainers(clientRetriever CosmosDBClientRetriever) (mcp.Tool, server.ToolHandlerFunc) {

	return listContainers(), func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {

		account, ok := request.Params.Arguments["account"].(string)
		if !ok || account == "" {
			return nil, errors.New("cosmos db account name missing")
		}
		database, ok := request.Params.Arguments["database"].(string)
		if !ok || database == "" {
			return nil, errors.New("database name missing")
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
		// databaseClient, err := common.GetDatabaseClient(account, database)
		// if err != nil {
		// 	return nil, fmt.Errorf("error creating Cosmos client: %v", err)
		// }

		containerPager := databaseClient.NewQueryContainersPager("select * from c", nil)

		containerNames := []string{}

		for containerPager.More() {
			containerResponse, err := containerPager.NextPage(context.Background())
			if err != nil {
				var responseErr *azcore.ResponseError
				errors.As(err, &responseErr)
				return nil, err
			}

			for _, container := range containerResponse.Containers {
				containerNames = append(containerNames, container.ID)
			}
		}

		// result := map[string]interface{}{
		// 	"containers": containerNames,
		// }

		jsonResult, err := json.Marshal(ListContainersResponse{
			Account:    account,
			Database:   database,
			Containers: containerNames,
		})

		if err != nil {
			return nil, fmt.Errorf("error marshalling result to JSON: %v", err)
		}

		return mcp.NewToolResultText(string(jsonResult)), nil
	}
}

type ListContainersResponse struct {
	Account    string
	Database   string
	Containers []string `json:"containers"`
}

func listContainers() mcp.Tool {

	return mcp.NewTool("list_containers",
		mcp.WithString("account",
			mcp.Required(),
			mcp.Description(ACCOUNT_PARAMETER_DESCRIPTION),
		),
		mcp.WithString("database",
			mcp.Required(),
			mcp.Description("Name of the database to list containers from"),
		),
		mcp.WithDescription("List all containers in a specific database"),
	)
}

func ReadContainerMetadata(clientRetriever CosmosDBClientRetriever) (mcp.Tool, server.ToolHandlerFunc) {
	return readContainerMetadata(), func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {

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

		// containerClient, err := common.GetContainerClient(account, database, container)
		// if err != nil {
		// 	return nil, fmt.Errorf("error creating container client: %v", err)
		// }

		response, err := containerClient.Read(context.Background(), nil)
		if err != nil {
			var responseErr *azcore.ResponseError
			errors.As(err, &responseErr)
			return nil, err
		}

		metadata := map[string]interface{}{
			"container_id":               response.ContainerProperties.ID,
			"default_ttl":                response.ContainerProperties.DefaultTimeToLive,
			"indexing_policy":            response.ContainerProperties.IndexingPolicy,
			"partition_key_definition":   response.ContainerProperties.PartitionKeyDefinition,
			"conflict_resolution_policy": response.ContainerProperties.ConflictResolutionPolicy,
		}

		jsonResult, err := json.Marshal(metadata)
		if err != nil {
			return nil, fmt.Errorf("error marshalling result to JSON: %v", err)
		}

		return mcp.NewToolResultText(string(jsonResult)), nil
	}
}

func readContainerMetadata() mcp.Tool {

	return mcp.NewTool(READ_CONTAINER_METADATA_TOOL_NAME,
		mcp.WithString("account",
			mcp.Required(),
			mcp.Description("Name of the Cosmos DB account"),
		),
		mcp.WithString("database",
			mcp.Required(),
			mcp.Description("Name of the database to list containers from"),
		),
		mcp.WithString("container",
			mcp.Required(),
			mcp.Description("Name of the container to query"),
		),
		mcp.WithDescription("Retrieve metadata or configuration of a specific container in a Cosmos DB database. Not to be used for executing queries or reading data from the container."),
	)
}

func CreateContainer(clientRetriever CosmosDBClientRetriever) (mcp.Tool, server.ToolHandlerFunc) {
	return createContainer(), func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
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
		partitionKeyPath, ok := request.Params.Arguments["partitionKeyPath"].(string)
		if !ok || partitionKeyPath == "" {
			return nil, errors.New("partition key path missing")
		}
		throughput, hasThroughput := request.Params.Arguments["throughput"].(int)

		client, err := clientRetriever.Get(account)

		if err != nil {
			fmt.Printf("Error creating Cosmos client: %v\n", err)
			return nil, err
		}

		databaseClient, err := client.NewDatabase(database)
		if err != nil {
			return nil, fmt.Errorf("error creating database client: %v", err)
		}
		// databaseClient, err := common.GetDatabaseClient(account, database)
		// if err != nil {
		// 	return nil, fmt.Errorf("error creating database client: %v", err)
		// }

		properties := azcosmos.ContainerProperties{
			ID: container,
			PartitionKeyDefinition: azcosmos.PartitionKeyDefinition{
				Paths: []string{partitionKeyPath},
				//Kind:  azcosmos.PartitionKeyKindHash,
			},
		}

		if hasThroughput {
			throughputProps := azcosmos.NewManualThroughputProperties(int32(throughput))
			_, err = databaseClient.CreateContainer(ctx, properties, &azcosmos.CreateContainerOptions{
				ThroughputProperties: &throughputProps,
			})
		} else {
			_, err = databaseClient.CreateContainer(ctx, properties, nil)
		}

		if err != nil {
			return nil, fmt.Errorf("error creating container: %v", err)
		}

		return mcp.NewToolResultText(fmt.Sprintf("Container '%s' created successfully in database '%s'", container, database)), nil
	}
}

func createContainer() mcp.Tool {
	return mcp.NewTool(CREATE_CONTAINER_TOOL_NAME,
		mcp.WithString("account",
			mcp.Required(),
			mcp.Description(ACCOUNT_PARAMETER_DESCRIPTION),
		),
		mcp.WithString("database",
			mcp.Required(),
			mcp.Description("Name of the database to create the container in"),
		),
		mcp.WithString("container",
			mcp.Required(),
			mcp.Description("Name of the container to create"),
		),
		mcp.WithString("partitionKeyPath",
			mcp.Required(),
			mcp.Description("Partition key path for the container, e.g., '/id'"),
		),
		mcp.WithNumber("throughput",
			mcp.Description("Provisioned throughput for the container (optional)"),
		),
		mcp.WithDescription("Create a new container in a specified database"),
	)
}

func AddItemToContainer(clientRetriever CosmosDBClientRetriever) (mcp.Tool, server.ToolHandlerFunc) {
	return addItemToContainer(), func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {

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
		partitionKeyValue, ok := request.Params.Arguments["partitionKey"].(string)
		if !ok || partitionKeyValue == "" {
			return nil, errors.New("value for partition key missing")
		}
		itemJSON, ok := request.Params.Arguments["item"].(string)
		if !ok || itemJSON == "" {
			return nil, errors.New("item JSON missing")
		}

		// var item map[string]interface{}
		// if err := json.Unmarshal([]byte(itemJSON), &item); err != nil {
		// 	return nil, fmt.Errorf("error unmarshalling item JSON: %v", err)
		// }

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
		// itemBytes, err := json.Marshal(item)
		// if err != nil {
		// 	return nil, fmt.Errorf("error marshalling item to JSON: %v", err)
		// }

		_, err = containerClient.CreateItem(ctx, partitionKey, []byte(itemJSON), nil)
		if err != nil {
			return nil, fmt.Errorf("error adding item to container: %v", err)
		}

		// var response map[string]interface{}
		// err = json.Unmarshal(createItemResponse.Value, &response)
		// if err != nil {
		// 	return nil, fmt.Errorf("error un-marshalling result: %v", err)
		// }

		return mcp.NewToolResultText(fmt.Sprintf("Item added successfully to container '%s' in database '%s'", container, database)), nil

		// return mcp.NewToolResultText(string(createItemResponse.Value)), nil
	}

}

func addItemToContainer() mcp.Tool {
	return mcp.NewTool(ADD_CONTAINER_ITEM_TOOL_NAME,
		mcp.WithString("account",
			mcp.Required(),
			mcp.Description(ACCOUNT_PARAMETER_DESCRIPTION),
		),
		mcp.WithString("database",
			mcp.Required(),
			mcp.Description("Name of the database to add the item to"),
		),
		mcp.WithString("container",
			mcp.Required(),
			mcp.Description("Name of the container to add the item to"),
		),
		mcp.WithString("partitionKey",
			mcp.Required(),
			mcp.Description("Partition key for the item to add"),
		),
		mcp.WithString("item",
			mcp.Required(),
			mcp.Description("The JSON representation of the item to add. id field is mandatory"),
		),
		mcp.WithDescription("Add a new item to a specified container in a Cosmos DB database"),
	)
}
