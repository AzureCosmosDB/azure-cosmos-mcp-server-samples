package tools

import (
	"context"
	"crypto/tls"
	"errors"
	"fmt"
	"net/http"
	"testing"
	"time"

	"github.com/Azure/azure-sdk-for-go/sdk/azcore"
	"github.com/Azure/azure-sdk-for-go/sdk/azcore/to"
	"github.com/Azure/azure-sdk-for-go/sdk/azcore/tracing"
	"github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos"
	"github.com/docker/go-connections/nat"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"
)

const (
	testOperationDBName        = "testDatabase"
	testOperationContainerName = "testContainer"
	testPartitionKey           = "/id"
	//emulatorImage              = "mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview"
	emulatorImage    = "mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest"
	emulatorPort     = "8081"
	emulatorEndpoint = "https://localhost:8081"
	emulatorKey      = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
)

var (
	emulator testcontainers.Container
)

// setupCosmosEmulator creates a CosmosDB emulator container for testing
func setupCosmosEmulator(ctx context.Context) (testcontainers.Container, error) {
	req := testcontainers.ContainerRequest{
		Image: emulatorImage,
		//ExposedPorts: []string{emulatorPort + ":8081", "10250-10255:10250-10255"},
		ExposedPorts: []string{emulatorPort + ":8081"},
		WaitingFor:   wait.ForListeningPort(nat.Port(emulatorPort)),
		Env: map[string]string{
			"AZURE_COSMOS_EMULATOR_PARTITION_COUNT": "5",
		},
	}

	container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: req,
		Started:          true,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to start container: %w", err)
	}

	// Give the emulator a bit more time to fully initialize
	time.Sleep(5 * time.Second)

	return container, nil
}

type CosmosDBEmulatorClientRetriever struct {
}

// setupCosmosClient creates a Cosmos DB client for the emulator

func (retriever CosmosDBEmulatorClientRetriever) Get(account string) (*azcosmos.Client, error) {
	// account is ignored

	transport := &http.Client{Transport: &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}}

	options := &azcosmos.ClientOptions{ClientOptions: azcore.ClientOptions{
		TracingProvider: tracing.Provider{},
		Transport:       transport,
	}}

	// Create credential with the emulator key
	cred, err := azcosmos.NewKeyCredential(emulatorKey)
	if err != nil {
		return nil, fmt.Errorf("failed to create key credential: %w", err)
	}

	// Create the client
	client, err := azcosmos.NewClientWithKey(emulatorEndpoint, cred, options)
	if err != nil {
		return nil, fmt.Errorf("failed to create cosmos client: %w", err)
	}

	return client, nil
}

// setupDatabaseAndContainer ensures the test database and container exist
func setupDatabaseAndContainer(ctx context.Context, client *azcosmos.Client) error {
	// Try to create the test database
	databaseProps := azcosmos.DatabaseProperties{ID: testOperationDBName}
	_, err := client.CreateDatabase(ctx, databaseProps, nil)
	if err != nil && !isResourceExistsError(err) {
		return fmt.Errorf("failed to create test database: %w", err)
	}

	// Create container if it doesn't exist
	database, err := client.NewDatabase(testOperationDBName)
	if err != nil {
		return fmt.Errorf("failed to get database: %w", err)
	}

	containerProps := azcosmos.ContainerProperties{
		ID: testOperationContainerName,
		PartitionKeyDefinition: azcosmos.PartitionKeyDefinition{
			Paths: []string{testPartitionKey},
		},
		DefaultTimeToLive: to.Ptr[int32](60), // Short TTL for test data (60 seconds)
	}

	_, err = database.CreateContainer(ctx, containerProps, nil)
	if err != nil && !isResourceExistsError(err) {
		return fmt.Errorf("failed to create test container: %w", err)
	}

	return nil
}

// isResourceExistsError checks if error is because resource already exists (status code 409)
func isResourceExistsError(err error) bool {
	var responseErr *azcore.ResponseError
	if errors.As(err, &responseErr) {
		return responseErr.StatusCode == 409
	}
	return false
}

func getTextFromToolResult(t *testing.T, result *mcp.CallToolResult) string {
	t.Helper()
	content := result.Content[0]
	text, _ := result.Content[0].(mcp.TextContent)
	assert.NotNil(t, content)
	require.IsType(t, mcp.TextContent{}, content)
	assert.Equal(t, "text", text.Type)

	return text.Text
}

// cleanupTestData removes test data after tests
func cleanupTestData(ctx context.Context, t *testing.T, client *azcosmos.Client, userID, sessionID string) {
	t.Helper()
	database, err := client.NewDatabase(testOperationDBName)
	if err != nil {
		return
	}

	container, err := database.NewContainer(testOperationContainerName)
	if err != nil {
		return
	}

	// Delete the test item
	_, _ = container.DeleteItem(ctx, azcosmos.NewPartitionKeyString(userID), sessionID, nil)
}
