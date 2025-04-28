package tools

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/Azure/azure-sdk-for-go/sdk/azcore"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func ListDatabases(clientRetriever CosmosDBClientRetriever) (mcp.Tool, server.ToolHandlerFunc) {
	//func ListDatabases() (mcp.Tool, server.ToolHandlerFunc) {

	return listDatabases(), func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {

		account, ok := request.Params.Arguments["account"].(string)
		if !ok || account == "" {
			return nil, errors.New("cosmos db account name missing")
		}

		client, err := clientRetriever.Get(account)
		//client, err := common.GetCosmosDBClient(account)

		if err != nil {
			fmt.Printf("Error creating Cosmos client: %v\n", err)
			return nil, err
		}

		databaseNames := []string{}

		queryPager := client.NewQueryDatabasesPager("select * from dbs d", nil)

		for queryPager.More() {
			queryResponse, err := queryPager.NextPage(context.Background())
			if err != nil {
				var responseErr *azcore.ResponseError
				errors.As(err, &responseErr)
				return nil, err
			}

			for _, db := range queryResponse.Databases {
				databaseNames = append(databaseNames, db.ID)
			}
		}

		jsonResult, err := json.Marshal(ListDatabasesResponse{Databases: databaseNames})
		if err != nil {
			return nil, fmt.Errorf("error marshalling result to JSON: %v", err)
		}

		return mcp.NewToolResultText(string(jsonResult)), nil
	}

}

type ListDatabasesResponse struct {
	Databases []string `json:"databases"`
}

func listDatabases() mcp.Tool {

	return mcp.NewTool(LIST_DATABASES_TOOL_NAME,
		mcp.WithString("account",
			mcp.Required(),
			mcp.Description(ACCOUNT_PARAMETER_DESCRIPTION),
		),
		mcp.WithDescription("List all databases in a Cosmos DB account"),
	)
}
