package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"testing"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

const dummy_account_does_not_matter = "dummy_account_does_not_matter"

func TestListDatabases(t *testing.T) {

	tool, handler := ListDatabases(CosmosDBEmulatorClientRetriever{})

	assert.Equal(t, tool.Name, LIST_DATABASES_TOOL_NAME)
	assert.NotEmpty(t, tool.Description)
	assert.Contains(t, tool.InputSchema.Properties, "account")
	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"account"})

	tests := []struct {
		name           string
		arguments      map[string]interface{}
		expectError    bool
		expectedResult string
		expectedErrMsg string
	}{
		{
			name: "valid account name",
			arguments: map[string]interface{}{
				"account": dummy_account_does_not_matter,
			},
			expectError:    false,
			expectedResult: testOperationDBName,
		},
		{
			name: "empty account name",
			arguments: map[string]interface{}{
				"account": "",
			},
			expectError:    true,
			expectedErrMsg: "cosmos db account name missing",
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			req := mcp.CallToolRequest{
				Params: struct {
					Name      string                 `json:"name"`
					Arguments map[string]interface{} `json:"arguments,omitempty"`
					Meta      *struct {
						ProgressToken mcp.ProgressToken `json:"progressToken,omitempty"`
					} `json:"_meta,omitempty"`
				}{
					Arguments: test.arguments,
				},
			}

			result, err := handler(context.Background(), req)
			if test.expectError {
				require.Error(t, err)
				assert.Contains(t, err.Error(), test.expectedErrMsg)
				return
			}

			require.NoError(t, err)

			textResult := getTextFromToolResult(t, result)

			var response ListDatabasesResponse
			err = json.Unmarshal([]byte(textResult), &response)
			require.NoError(t, err)
			assert.Equal(t, 1, len(response.Databases))
			assert.Equal(t, test.expectedResult, response.Databases[0])
		})
	}

}

func TestListContainers(t *testing.T) {

	tool, handler := ListContainers(CosmosDBEmulatorClientRetriever{})

	assert.Equal(t, tool.Name, LIST_CONTAINERS_TOOL_NAME)
	assert.NotEmpty(t, tool.Description)
	assert.Contains(t, tool.InputSchema.Properties, "account")
	assert.Contains(t, tool.InputSchema.Properties, "database")

	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"account", "database"})

	tests := []struct {
		name           string
		arguments      map[string]interface{}
		expectError    bool
		expectedResult string
		expectedErrMsg string
	}{
		{
			name: "valid arguments",
			arguments: map[string]interface{}{
				"account":  dummy_account_does_not_matter,
				"database": testOperationDBName,
			},
			expectError:    false,
			expectedResult: testOperationContainerName,
		},
		{
			name: "empty account name",
			arguments: map[string]interface{}{
				"account":  "",
				"database": testOperationDBName,
			},
			expectError:    true,
			expectedErrMsg: "cosmos db account name missing",
		},
		{
			name: "empty database name",
			arguments: map[string]interface{}{
				"account":  dummy_account_does_not_matter,
				"database": "",
			},
			expectError:    true,
			expectedErrMsg: "database name missing",
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			req := mcp.CallToolRequest{
				Params: struct {
					Name      string                 `json:"name"`
					Arguments map[string]interface{} `json:"arguments,omitempty"`
					Meta      *struct {
						ProgressToken mcp.ProgressToken `json:"progressToken,omitempty"`
					} `json:"_meta,omitempty"`
				}{
					Arguments: test.arguments,
				},
			}

			result, err := handler(context.Background(), req)
			if test.expectError {
				require.Error(t, err)
				assert.Contains(t, err.Error(), test.expectedErrMsg)
				return
			}

			require.NoError(t, err)

			textResult := getTextFromToolResult(t, result)

			var response ListContainersResponse
			err = json.Unmarshal([]byte(textResult), &response)
			require.NoError(t, err)

			assert.Equal(t, dummy_account_does_not_matter, response.Account)
			assert.Equal(t, testOperationDBName, response.Database)
			assert.Equal(t, 1, len(response.Containers))
			assert.Equal(t, test.expectedResult, response.Containers[0])
		})
	}
}

func TestReadContainerMetadata(t *testing.T) {
	tool, handler := ReadContainerMetadata(CosmosDBEmulatorClientRetriever{})

	assert.Equal(t, tool.Name, READ_CONTAINER_METADATA_TOOL_NAME)
	assert.NotEmpty(t, tool.Description)
	assert.Contains(t, tool.InputSchema.Properties, "account")
	assert.Contains(t, tool.InputSchema.Properties, "database")
	assert.Contains(t, tool.InputSchema.Properties, "container")
	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"account", "database", "container"})

	tests := []struct {
		name           string
		arguments      map[string]interface{}
		expectError    bool
		expectedErrMsg string
	}{
		{
			name: "valid arguments",
			arguments: map[string]interface{}{
				"account":   dummy_account_does_not_matter,
				"database":  testOperationDBName,
				"container": testOperationContainerName,
			},
			expectError: false,
		},
		{
			name: "empty account name",
			arguments: map[string]interface{}{
				"account":   "",
				"database":  testOperationDBName,
				"container": testOperationContainerName,
			},
			expectError:    true,
			expectedErrMsg: "cosmos db account name missing",
		},
		{
			name: "empty database name",
			arguments: map[string]interface{}{
				"account":   dummy_account_does_not_matter,
				"database":  "",
				"container": testOperationContainerName,
			},
			expectError:    true,
			expectedErrMsg: "database name missing",
		},
		{
			name: "empty container name",
			arguments: map[string]interface{}{
				"account":   dummy_account_does_not_matter,
				"database":  testOperationDBName,
				"container": "",
			},
			expectError:    true,
			expectedErrMsg: "container name missing",
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			req := mcp.CallToolRequest{
				Params: struct {
					Name      string                 `json:"name"`
					Arguments map[string]interface{} `json:"arguments,omitempty"`
					Meta      *struct {
						ProgressToken mcp.ProgressToken `json:"progressToken,omitempty"`
					} `json:"_meta,omitempty"`
				}{
					Arguments: test.arguments,
				},
			}

			result, err := handler(context.Background(), req)
			if test.expectError {
				require.Error(t, err)
				assert.Contains(t, err.Error(), test.expectedErrMsg)
				return
			}

			require.NoError(t, err)

			textResult := getTextFromToolResult(t, result)

			var metadata map[string]interface{}
			err = json.Unmarshal([]byte(textResult), &metadata)
			require.NoError(t, err)

			assert.Contains(t, metadata, "container_id")
			assert.Contains(t, metadata, "default_ttl")
			assert.Contains(t, metadata, "indexing_policy")
			assert.Contains(t, metadata, "partition_key_definition")
			assert.Contains(t, metadata, "conflict_resolution_policy")
		})
	}
}

func TestCreateContainer(t *testing.T) {
	tool, handler := CreateContainer(CosmosDBEmulatorClientRetriever{})

	assert.Equal(t, tool.Name, CREATE_CONTAINER_TOOL_NAME)
	assert.NotEmpty(t, tool.Description)
	assert.Contains(t, tool.InputSchema.Properties, "account")
	assert.Contains(t, tool.InputSchema.Properties, "database")
	assert.Contains(t, tool.InputSchema.Properties, "container")
	assert.Contains(t, tool.InputSchema.Properties, "partitionKeyPath")
	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"account", "database", "container", "partitionKeyPath"})

	tests := []struct {
		name           string
		arguments      map[string]interface{}
		expectedResult string
		expectError    bool
		expectedErrMsg string
	}{
		// in emulator, the valid create scenarios fail with - Sorry, we are currently experiencing high demand in this region South Central US, and cannot fulfill your request at this time
		// commenting out temporarily
		{
			name: "valid arguments",
			arguments: map[string]interface{}{
				"account":          dummy_account_does_not_matter,
				"database":         testOperationDBName,
				"container":        "testContainer_new_1",
				"partitionKeyPath": "/id",
			},
			expectedResult: fmt.Sprintf("Container '%s' created successfully in database '%s'", "testContainer_new_1", testOperationDBName),
			expectError:    false,
		},
		{
			name: "valid arguments with throughput",
			arguments: map[string]interface{}{
				"account":          dummy_account_does_not_matter,
				"database":         testOperationDBName,
				"container":        "testContainer_new_2",
				"partitionKeyPath": "/id",
				"throughput":       400,
			},
			expectedResult: fmt.Sprintf("Container '%s' created successfully in database '%s'", "testContainer_new_2", testOperationDBName),
			expectError:    false,
		},
		{
			name: "empty account name",
			arguments: map[string]interface{}{
				"account":          "",
				"database":         testOperationDBName,
				"container":        "testContainer",
				"partitionKeyPath": "/id",
			},
			expectError:    true,
			expectedErrMsg: "cosmos db account name missing",
		},
		{
			name: "empty database name",
			arguments: map[string]interface{}{
				"account":          dummy_account_does_not_matter,
				"database":         "",
				"container":        "testContainer",
				"partitionKeyPath": "/id",
			},
			expectError:    true,
			expectedErrMsg: "database name missing",
		},
		{
			name: "empty container name",
			arguments: map[string]interface{}{
				"account":          dummy_account_does_not_matter,
				"database":         testOperationDBName,
				"container":        "",
				"partitionKeyPath": "/id",
			},
			expectError:    true,
			expectedErrMsg: "container name missing",
		},
		{
			name: "empty partition key path",
			arguments: map[string]interface{}{
				"account":          dummy_account_does_not_matter,
				"database":         testOperationDBName,
				"container":        "testContainer",
				"partitionKeyPath": "",
			},
			expectError:    true,
			expectedErrMsg: "partition key path missing",
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			req := mcp.CallToolRequest{
				Params: struct {
					Name      string                 `json:"name"`
					Arguments map[string]interface{} `json:"arguments,omitempty"`
					Meta      *struct {
						ProgressToken mcp.ProgressToken `json:"progressToken,omitempty"`
					} `json:"_meta,omitempty"`
				}{
					Arguments: test.arguments,
				},
			}

			result, err := handler(context.Background(), req)
			if test.expectError {
				require.Error(t, err)
				assert.Contains(t, err.Error(), test.expectedErrMsg)
				return
			}

			require.NoError(t, err)

			textResult := getTextFromToolResult(t, result)
			assert.Equal(t, test.expectedResult, textResult)
			// assert.Contains(t, textResult, "Container '")
			// assert.Contains(t, textResult, "created successfully in database '")
		})
	}
}

func TestAddItemToContainer(t *testing.T) {
	tool, handler := AddItemToContainer(CosmosDBEmulatorClientRetriever{})

	assert.Equal(t, tool.Name, ADD_CONTAINER_ITEM_TOOL_NAME)
	assert.NotEmpty(t, tool.Description)
	assert.Contains(t, tool.InputSchema.Properties, "account")
	assert.Contains(t, tool.InputSchema.Properties, "database")
	assert.Contains(t, tool.InputSchema.Properties, "container")
	assert.Contains(t, tool.InputSchema.Properties, "partitionKey")
	assert.Contains(t, tool.InputSchema.Properties, "item")
	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"account", "database", "container", "partitionKey", "item"})

	tests := []struct {
		name           string
		arguments      map[string]interface{}
		expectError    bool
		expectedResult string
		expectedErrMsg string
	}{
		{
			name: "valid arguments",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"partitionKey": "user1",
				"item":         `{"id": "user1", "value": "user1@foo.com"}`,
			},
			expectedResult: fmt.Sprintf("Item added successfully to container '%s' in database '%s'", testOperationContainerName, testOperationDBName),
			expectError:    false,
		},
		{
			name: "invalid partition key",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"partitionKey": "1",
				"item":         `{"id": "testItem", "value": "testValue"}`,
			},
			expectError:    true,
			expectedErrMsg: "error adding item to container",
		},
		{
			name: "missing id attribute",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"partitionKey": "1",
				"item":         `{"value": "testValue"}`,
			},
			expectError:    true,
			expectedErrMsg: "error adding item to container",
		},
		{
			name: "empty account name",
			arguments: map[string]interface{}{
				"account":      "",
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"partitionKey": "testPartitionKey",
				"item":         `{"id": "testItem", "value": "testValue"}`,
			},
			expectError:    true,
			expectedErrMsg: "cosmos db account name missing",
		},
		{
			name: "empty database name",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     "",
				"container":    testOperationContainerName,
				"partitionKey": "testPartitionKey",
				"item":         `{"id": "testItem", "value": "testValue"}`,
			},
			expectError:    true,
			expectedErrMsg: "database name missing",
		},
		{
			name: "empty container name",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    "",
				"partitionKey": "testPartitionKey",
				"item":         `{"id": "testItem", "value": "testValue"}`,
			},
			expectError:    true,
			expectedErrMsg: "container name missing",
		},
		{
			name: "empty partition key",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"partitionKey": "",
				"item":         `{"id": "testItem", "value": "testValue"}`,
			},
			expectError:    true,
			expectedErrMsg: "value for partition key missing",
		},
		{
			name: "empty item",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"partitionKey": "testPartitionKey",
				"item":         "",
			},
			expectError:    true,
			expectedErrMsg: "item JSON missing",
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			req := mcp.CallToolRequest{
				Params: struct {
					Name      string                 `json:"name"`
					Arguments map[string]interface{} `json:"arguments,omitempty"`
					Meta      *struct {
						ProgressToken mcp.ProgressToken `json:"progressToken,omitempty"`
					} `json:"_meta,omitempty"`
				}{
					Arguments: test.arguments,
				},
			}

			result, err := handler(context.Background(), req)
			if test.expectError {
				require.Error(t, err)
				assert.Contains(t, err.Error(), test.expectedErrMsg)
				return
			}

			require.NoError(t, err)

			textResult := getTextFromToolResult(t, result)
			assert.Equal(t, test.expectedResult, textResult)
		})
	}
}

func TestReadItem(t *testing.T) {
	tool, handler := ReadItem(CosmosDBEmulatorClientRetriever{})

	assert.Equal(t, tool.Name, READ_ITEM_TOOL_NAME)
	assert.NotEmpty(t, tool.Description)
	assert.Contains(t, tool.InputSchema.Properties, "account")
	assert.Contains(t, tool.InputSchema.Properties, "database")
	assert.Contains(t, tool.InputSchema.Properties, "container")
	assert.Contains(t, tool.InputSchema.Properties, "itemID")
	assert.Contains(t, tool.InputSchema.Properties, "partitionKey")
	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"account", "database", "container", "itemID", "partitionKey"})

	id := "user2"
	partitionKeyValue := "user2"

	tool, addItemHandler := AddItemToContainer(CosmosDBEmulatorClientRetriever{})

	// need to add an item to the container first
	_, err := addItemHandler(context.Background(), mcp.CallToolRequest{
		Params: struct {
			Name      string                 `json:"name"`
			Arguments map[string]interface{} `json:"arguments,omitempty"`
			Meta      *struct {
				ProgressToken mcp.ProgressToken `json:"progressToken,omitempty"`
			} `json:"_meta,omitempty"`
		}{
			Arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"partitionKey": partitionKeyValue,
				"item":         `{"id": "user2", "value": "user2@foo.com"}`,
			},
		},
	})

	require.NoError(t, err)

	tests := []struct {
		name           string
		arguments      map[string]interface{}
		expectError    bool
		expectedErrMsg string
	}{
		{
			name: "valid arguments",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"itemID":       id,
				"partitionKey": partitionKeyValue,
			},
			expectError: false,
		},
		{
			name: "empty account name",
			arguments: map[string]interface{}{
				"account":      "",
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"itemID":       "testItem",
				"partitionKey": "testPartitionKey",
			},
			expectError:    true,
			expectedErrMsg: "cosmos db account name missing",
		},
		{
			name: "empty database name",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     "",
				"container":    testOperationContainerName,
				"itemID":       "testItem",
				"partitionKey": "testPartitionKey",
			},
			expectError:    true,
			expectedErrMsg: "database name missing",
		},
		{
			name: "empty container name",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    "",
				"itemID":       "testItem",
				"partitionKey": "testPartitionKey",
			},
			expectError:    true,
			expectedErrMsg: "container name missing",
		},
		{
			name: "empty item ID",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"itemID":       "",
				"partitionKey": "testPartitionKey",
			},
			expectError:    true,
			expectedErrMsg: "item ID missing",
		},
		{
			name: "empty partition key",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"itemID":       "testItem",
				"partitionKey": "",
			},
			expectError:    true,
			expectedErrMsg: "partition key missing",
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			req := mcp.CallToolRequest{
				Params: struct {
					Name      string                 `json:"name"`
					Arguments map[string]interface{} `json:"arguments,omitempty"`
					Meta      *struct {
						ProgressToken mcp.ProgressToken `json:"progressToken,omitempty"`
					} `json:"_meta,omitempty"`
				}{
					Arguments: test.arguments,
				},
			}

			result, err := handler(context.Background(), req)
			if test.expectError {
				require.Error(t, err)
				assert.Contains(t, err.Error(), test.expectedErrMsg)
				return
			}

			require.NoError(t, err)

			textResult := getTextFromToolResult(t, result)
			assert.NotEmpty(t, textResult)

			var item map[string]interface{}
			err = json.Unmarshal([]byte(textResult), &item)

			require.NoError(t, err)
			assert.Equal(t, id, item["id"].(string))
		})
	}
}

func TestExecuteQuery(t *testing.T) {
	tool, handler := ExecuteQuery(CosmosDBEmulatorClientRetriever{})

	assert.Equal(t, tool.Name, EXECUTE_QUERY_TOOL_NAME)
	assert.NotEmpty(t, tool.Description)
	assert.Contains(t, tool.InputSchema.Properties, "account")
	assert.Contains(t, tool.InputSchema.Properties, "database")
	assert.Contains(t, tool.InputSchema.Properties, "container")
	assert.Contains(t, tool.InputSchema.Properties, "query")
	assert.ElementsMatch(t, tool.InputSchema.Required, []string{"account", "database", "container", "query"})

	//id := "user3"
	partitionKeyValue := "user3"

	tool, addItemHandler := AddItemToContainer(CosmosDBEmulatorClientRetriever{})

	// need to add an item to the container first
	_, err := addItemHandler(context.Background(), mcp.CallToolRequest{
		Params: struct {
			Name      string                 `json:"name"`
			Arguments map[string]interface{} `json:"arguments,omitempty"`
			Meta      *struct {
				ProgressToken mcp.ProgressToken `json:"progressToken,omitempty"`
			} `json:"_meta,omitempty"`
		}{
			Arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"partitionKey": partitionKeyValue,
				"item":         `{"id": "user3", "value": "user3@foo.com"}`,
			},
		},
	})

	require.NoError(t, err)

	tests := []struct {
		name           string
		arguments      map[string]interface{}
		expectError    bool
		expectedErrMsg string
	}{
		{
			name: "valid arguments",
			arguments: map[string]interface{}{
				"account":      dummy_account_does_not_matter,
				"database":     testOperationDBName,
				"container":    testOperationContainerName,
				"query":        "SELECT * FROM c",
				"partitionKey": partitionKeyValue,
			},
			expectError: false,
		},
		{
			name: "valid arguments - no partition key",
			arguments: map[string]interface{}{
				"account":   dummy_account_does_not_matter,
				"database":  testOperationDBName,
				"container": testOperationContainerName,
				"query":     "SELECT * FROM c",
			},
			expectError: false,
		},
		{
			name: "empty account name",
			arguments: map[string]interface{}{
				"account":   "",
				"database":  testOperationDBName,
				"container": testOperationContainerName,
				"query":     "SELECT * FROM c",
			},
			expectError:    true,
			expectedErrMsg: "cosmos db account name missing",
		},
		{
			name: "empty database name",
			arguments: map[string]interface{}{
				"account":   dummy_account_does_not_matter,
				"database":  "",
				"container": testOperationContainerName,
				"query":     "SELECT * FROM c",
			},
			expectError:    true,
			expectedErrMsg: "database name missing",
		},
		{
			name: "empty container name",
			arguments: map[string]interface{}{
				"account":   dummy_account_does_not_matter,
				"database":  testOperationDBName,
				"container": "",
				"query":     "SELECT * FROM c",
			},
			expectError:    true,
			expectedErrMsg: "container name missing",
		},
		{
			name: "empty query string",
			arguments: map[string]interface{}{
				"account":   dummy_account_does_not_matter,
				"database":  testOperationDBName,
				"container": testOperationContainerName,
				"query":     "",
			},
			expectError:    true,
			expectedErrMsg: "query string missing",
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			req := mcp.CallToolRequest{
				Params: struct {
					Name      string                 `json:"name"`
					Arguments map[string]interface{} `json:"arguments,omitempty"`
					Meta      *struct {
						ProgressToken mcp.ProgressToken `json:"progressToken,omitempty"`
					} `json:"_meta,omitempty"`
				}{
					Arguments: test.arguments,
				},
			}

			result, err := handler(context.Background(), req)
			if test.expectError {
				require.Error(t, err)
				assert.Contains(t, err.Error(), test.expectedErrMsg)
				return
			}

			require.NoError(t, err)

			textResult := getTextFromToolResult(t, result)
			assert.NotEmpty(t, textResult)

			var response ExecuteQueryResponse
			err = json.Unmarshal([]byte(textResult), &response)
			require.NoError(t, err)
			assert.NotEmpty(t, response.QueryResults)
			assert.NotEmpty(t, response.QueryMetrics)
		})
	}
}

func TestMain(m *testing.M) {
	// Set up the CosmosDB emulator container
	ctx := context.Background()
	var err error
	emulator, err = setupCosmosEmulator(ctx)
	if err != nil {
		fmt.Printf("Failed to set up CosmosDB emulator: %v\n", err)
		os.Exit(1)
	}

	// Set up the CosmosDB client
	client, err := CosmosDBEmulatorClientRetriever{}.Get(dummy_account_does_not_matter)
	if err != nil {
		fmt.Printf("Failed to set up CosmosDB client: %v\n", err)
		os.Exit(1)
	}

	// Set up the database and container
	err = setupDatabaseAndContainer(ctx, client)
	if err != nil {
		fmt.Printf("Failed to set up database and container: %v\n", err)
		os.Exit(1)
	}

	// Run the tests
	code := m.Run()

	// Tear down the CosmosDB emulator container
	if emulator != nil {
		_ = emulator.Terminate(ctx)
	}

	os.Exit(code)
}
