#!/usr/bin/env python3
"""
Azure Cosmos DB MCP Server (Streamable HTTP)

A Model Context Protocol (MCP) server implementation for Azure Cosmos DB,
providing tools for querying and exploring Cosmos DB containers via HTTP.
"""

import argparse
import json
import logging
import os
import sys
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from azure.cosmos import CosmosClient, exceptions
load_dotenv()

from fastmcp import FastMCP

try:
    from azure.identity import DefaultAzureCredential
    AZURE_IDENTITY_AVAILABLE = True
except ImportError:
    AZURE_IDENTITY_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cosmos-mcp-server')

# Version information
__version__ = "0.3.0"
__author__ = "Mohammed Ashfaq"
__email__ = "ash001x@gmail.com"
__license__ = "MIT"


class CosmosDBConnection:
    """Manages the connection to Azure Cosmos DB."""
    
    def __init__(self, uri: str, key: Optional[str], database: str, container: str, use_managed_identity: bool = False):
        """
        Initialize Cosmos DB connection parameters.
        
        Args:
            uri: Cosmos DB account URI
            key: Cosmos DB account key (optional if using Managed Identity)
            database: Database name
            container: Default container name
            use_managed_identity: Use Azure Managed Identity for authentication
        """
        self.uri = uri
        self.key = key
        self.database = database
        self.default_container = container
        self.use_managed_identity = use_managed_identity
        self._client = None
        self._database_client = None
    
    def get_client(self) -> CosmosClient:
        """Get or create the Cosmos DB client."""
        if not self._client:
            if self.use_managed_identity:
                if not AZURE_IDENTITY_AVAILABLE:
                    raise RuntimeError(
                        "Azure Managed Identity requested but azure-identity package not installed. "
                        "Install with: pip install azure-identity"
                    )
                credential = DefaultAzureCredential()
                self._client = CosmosClient(self.uri, credential=credential)
                logger.info("Connected to Cosmos DB using Azure Managed Identity")
            else:
                if not self.key:
                    raise RuntimeError("Access key required when not using Managed Identity")
                self._client = CosmosClient(self.uri, credential=self.key)
                logger.info("Connected to Cosmos DB using access key")
        return self._client
    
    def get_database_client(self):
        """Get or create the database client."""
        if not self._database_client:
            self._database_client = self.get_client().get_database_client(self.database)
        return self._database_client
    
    def get_container_client(self, container_name: Optional[str] = None):
        """
        Get a container client.
        
        Args:
            container_name: Name of the container, defaults to the configured container
            
        Returns:
            Container client instance
            
        Raises:
            RuntimeError: If connection parameters are missing
        """
        if not self.uri or not self.database or not self.default_container:
            raise RuntimeError(
                "Missing Cosmos DB connection parameters. "
                "Please provide URI, database, and container."
            )
        
        try:
            container = container_name or self.default_container
            return self.get_database_client().get_container_client(container)
        except Exception as e:
            logger.error(f"Failed to connect to CosmosDB container: {str(e)}")
            raise


# Global connection instance
cosmos_connection = None


def initialize_server() -> FastMCP:
    """Initialize the FastMCP server with Cosmos DB tools."""
    return FastMCP(
        "Azure Cosmos DB Explorer",
        version=__version__,
        capabilities={
            "tools": True,
            "logging": True,
            "resources": False,
            "prompts": False
        }
    )


# Initialize MCP server
mcp = initialize_server()


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for Cosmos DB configuration."""
    parser = argparse.ArgumentParser(
        description="Azure Cosmos DB MCP Server (Streamable HTTP) - Enables LLM interaction with Cosmos DB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  COSMOS_URI        Cosmos DB account URI
  COSMOS_KEY        Cosmos DB account key
  COSMOS_DATABASE   Database name
  COSMOS_CONTAINER  Default container name

Example:
  python cosmos_mcp_server.py --uri https://myaccount.documents.azure.com:443/ \\
                              --key <key> --db mydb --container mycontainer \\
                              --host localhost --port 8000
        """
    )
    
    parser.add_argument(
        "--uri",
        dest="uri",
        default=os.getenv("COSMOS_URI"),
        help="Cosmos DB URI (can also be set via COSMOS_URI env var)"
    )
    parser.add_argument(
        "--key",
        dest="key",
        default=os.getenv("COSMOS_KEY"),
        help="Cosmos DB Key (can also be set via COSMOS_KEY env var)"
    )
    parser.add_argument(
        "--db",
        dest="db",
        default=os.getenv("COSMOS_DATABASE"),
        help="Database name (can also be set via COSMOS_DATABASE env var)"
    )
    parser.add_argument(
        "--container",
        dest="container",
        default=os.getenv("COSMOS_CONTAINER"),
        help="Container name (can also be set via COSMOS_CONTAINER env var)"
    )
    parser.add_argument(
        "--host",
        dest="host",
        default=os.getenv("MCP_HOST", "localhost"),
        help="Host to bind the HTTP server (default: localhost)"
    )
    parser.add_argument(
        "--port",
        dest="port",
        type=int,
        default=int(os.getenv("MCP_PORT", "8000")),
        help="Port to bind the HTTP server (default: 8000)"
    )
    parser.add_argument(
        "--use-managed-identity",
        action="store_true",
        help="Use Azure Managed Identity for authentication instead of access key"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    return parser.parse_args()


def format_query_results(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format query results as JSON for streamable HTTP transport.
    
    Args:
        items: List of documents from query
        
    Returns:
        Dictionary with results and metadata
    """
    return {
        "count": len(items),
        "results": items
    }


@mcp.tool()
def query_cosmos(query: str, container_name: Optional[str] = None) -> str:
    """
    Run an arbitrary SQL-like query on the CosmosDB container and return JSON results.
    
    This is the primary tool for querying data. Use SELECT queries to fetch specific records.
    Example: "SELECT * FROM c WHERE c.City = 'Miami'"
    
    Args:
        query: SQL-like query string (required)
        container_name: Name of container (optional, uses default if not provided)
        
    Returns:
        JSON string with query results or error message
    """
    try:
        container = cosmos_connection.get_container_client(container_name)
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        result = format_query_results(items)
        return json.dumps(result, default=str)
    except exceptions.CosmosHttpResponseError as e:
        error_result = {"error": f"Cosmos DB error: {e.status_code} - {e.message}"}
        return json.dumps(error_result)
    except Exception as e:
        error_result = {"error": f"Query error: {str(e)}"}
        return json.dumps(error_result)


@mcp.tool()
def list_collections() -> str:
    """
    List all container (collection) names present in the current CosmosDB database.
    
    Useful for discovering available data tables.
    
    Returns:
        JSON string with list of container names or error message
    """
    try:
        db_client = cosmos_connection.get_database_client()
        containers = list(db_client.list_containers())
        
        container_names = [c['id'] for c in containers]
        result = {
            "count": len(container_names),
            "containers": container_names
        }
        return json.dumps(result)
    except Exception as e:
        error_result = {"error": f"Error listing containers: {str(e)}"}
        return json.dumps(error_result)


@mcp.tool()
def describe_container(container_name: Optional[str] = None) -> str:
    """
    Describe the schema of a container by inspecting a sample document.
    
    Outputs field names and types to help understand the structure.
    Useful for building queries when no schema is predefined.
    
    Args:
        container_name: Name of container to describe (optional, uses default if not provided)
        
    Returns:
        JSON string with schema description or error message
    """
    try:
        container = cosmos_connection.get_container_client(container_name)
        
        # Get a sample document
        sample_query = "SELECT * FROM c OFFSET 0 LIMIT 1"
        items = list(container.query_items(
            query=sample_query,
            enable_cross_partition_query=True
        ))
        
        if not items:
            result = {
                "error": f"No documents found in container '{container_name or cosmos_connection.default_container}'"
            }
            return json.dumps(result)
        
        sample = items[0]
        
        # Build schema description
        fields = []
        for key, value in sample.items():
            fields.append({
                "name": key,
                "type": type(value).__name__,
                "sample_value": str(value)[:100] if not isinstance(value, (dict, list)) else f"{type(value).__name__}"
            })
        
        result = {
            "container": container_name or cosmos_connection.default_container,
            "field_count": len(fields),
            "fields": fields
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        error_result = {"error": f"Error describing container: {str(e)}"}
        return json.dumps(error_result)


@mcp.tool()
def find_implied_links(container_name: Optional[str] = None) -> str:
    """
    Detect relationship hints in a container by analyzing field name patterns.
    
    This tool helps infer foreign-key-like fields (e.g., `user_id`, `property_fk`),
    useful for understanding relationships.
    
    Args:
        container_name: Name of container to analyze (optional)
        
    Returns:
        JSON string with detected relationship patterns or message
    """
    try:
        container = cosmos_connection.get_container_client(container_name)
        
        # Sample documents to analyze patterns
        sample_query = "SELECT * FROM c OFFSET 0 LIMIT 10"
        items = list(container.query_items(
            query=sample_query,
            enable_cross_partition_query=True
        ))
        
        if not items:
            result = {"message": "No documents found to analyze"}
            return json.dumps(result)
        
        # Analyze field patterns
        relationship_hints = set()
        id_fields = set()
        
        for doc in items:
            for key in doc:
                key_lower = key.lower()
                
                # Check for common foreign key patterns
                if key_lower.endswith(('_id', 'id', '_fk', '_ref', '_key')):
                    if key_lower not in ('id', '_id'):  # Exclude document ID
                        relationship_hints.add(key)
                
                # Check for ID-like fields
                if 'id' in key_lower:
                    id_fields.add(key)
        
        result = {
            "container": container_name or cosmos_connection.default_container,
            "foreign_key_candidates": sorted(list(relationship_hints)),
            "id_fields": sorted(list(id_fields))
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        error_result = {"error": f"Error analyzing relationships: {str(e)}"}
        return json.dumps(error_result)


@mcp.tool()
def get_sample_documents(container_name: Optional[str] = None, limit: int = 5) -> str:
    """
    Retrieve a small number of sample documents from a container to preview real data.
    
    Use this to inspect actual entries and understand data content before querying.
    
    Args:
        container_name: Name of container (optional)
        limit: Number of documents to retrieve (default: 5, max: 100)
        
    Returns:
        JSON string with sample documents or error message
    """
    try:
        if limit < 1 or limit > 100:
            result = {"error": "Limit must be between 1 and 100"}
            return json.dumps(result)
        
        container = cosmos_connection.get_container_client(container_name)
        query = f"SELECT * FROM c OFFSET 0 LIMIT {limit}"
        docs = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        result = {
            "container": container_name or cosmos_connection.default_container,
            "count": len(docs),
            "documents": docs
        }
        
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        error_result = {"error": f"Error fetching documents: {str(e)}"}
        return json.dumps(error_result)


@mcp.tool()
def count_documents(filters: Optional[Dict[str, Any]] = None, container_name: Optional[str] = None) -> str:
    """
    Count documents in the CosmosDB container, optionally with equality filters.
    
    Args:
        filters: Optional dictionary of field:value pairs for exact match filtering (e.g., {"City": "Miami", "Status": "Active"})
        container_name: Name of container (optional)
        
    Returns:
        JSON string with document count or error message
    """
    try:
        container = cosmos_connection.get_container_client(container_name)
        
        # Build query based on filters
        if filters and isinstance(filters, dict):
            where_clauses = []
            for field, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"c.{field} = '{value}'")
                elif isinstance(value, bool):
                    where_clauses.append(f"c.{field} = {str(value).lower()}")
                elif value is None:
                    where_clauses.append(f"IS_NULL(c.{field})")
                else:
                    where_clauses.append(f"c.{field} = {value}")
            
            where_clause = " AND ".join(where_clauses)
            count_query = f"SELECT VALUE COUNT(1) FROM c WHERE {where_clause}"
        else:
            count_query = "SELECT VALUE COUNT(1) FROM c"
        
        result_list = list(container.query_items(
            query=count_query,
            enable_cross_partition_query=True
        ))
        
        count = result_list[0] if result_list else 0
        
        result = {
            "container": container_name or cosmos_connection.default_container,
            "count": count,
            "filters": filters or {}
        }
        
        return json.dumps(result)
    except Exception as e:
        error_result = {"error": f"Error counting documents: {str(e)}"}
        return json.dumps(error_result)


@mcp.tool()
def get_partition_key_info(container_name: Optional[str] = None) -> str:
    """
    Get the partition key path of the CosmosDB container.
    
    Useful when you need to optimize queries or understand how data is distributed.
    
    Args:
        container_name: Name of container (optional)
        
    Returns:
        JSON string with partition key information or error message
    """
    try:
        container = cosmos_connection.get_container_client(container_name)
        properties = container.read()
        
        partition_key = properties.get('partitionKey', {})
        
        result = {
            "container": container_name or cosmos_connection.default_container,
            "partition_key": {
                "paths": partition_key.get('paths', []),
                "kind": partition_key.get('kind', 'Hash'),
                "version": partition_key.get('version', 1)
            }
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        error_result = {"error": f"Error fetching partition key: {str(e)}"}
        return json.dumps(error_result)


@mcp.tool()
def get_indexing_policy(container_name: Optional[str] = None) -> str:
    """
    Retrieve and display the indexing policy of the CosmosDB container.
    
    Indexing policies define how queries perform; useful for optimization/debugging.
    
    Args:
        container_name: Name of container (optional)
        
    Returns:
        JSON string with indexing policy or error message
    """
    try:
        container = cosmos_connection.get_container_client(container_name)
        properties = container.read()
        
        indexing_policy = properties.get('indexingPolicy', {})
        
        result = {
            "container": container_name or cosmos_connection.default_container,
            "indexing_policy": indexing_policy
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        error_result = {"error": f"Error retrieving indexing policy: {str(e)}"}
        return json.dumps(error_result)


@mcp.tool()
def list_distinct_values(field_name: str, container_name: Optional[str] = None, limit: int = 100) -> str:
    """
    List unique values for a given field in the container.
    
    Helps with filter creation, cardinality checks, and data discovery.
    
    Args:
        field_name: Name of the field to get distinct values for (required)
        container_name: Name of container (optional)
        limit: Maximum number of distinct values to return (default: 100, max: 1000)
        
    Returns:
        JSON string with list of distinct values or error message
    """
    try:
        if limit < 1 or limit > 1000:
            result = {"error": "Limit must be between 1 and 1000"}
            return json.dumps(result)
        
        container = cosmos_connection.get_container_client(container_name)
        
        # Query for distinct values
        query = f"SELECT DISTINCT VALUE c.{field_name} FROM c"
        values = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        # Sort values for better readability (handle different types)
        try:
            sorted_values = sorted(values, key=lambda x: (type(x).__name__, x))
        except TypeError:
            sorted_values = values
        
        # Apply limit
        limited_values = sorted_values[:limit]
        
        result = {
            "container": container_name or cosmos_connection.default_container,
            "field": field_name,
            "total_distinct": len(values),
            "returned_count": len(limited_values),
            "values": limited_values
        }
        
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        error_result = {"error": f"Error fetching distinct values: {str(e)}"}
        return json.dumps(error_result)


def validate_connection_params(args: argparse.Namespace) -> bool:
    """
    Validate that all required connection parameters are provided.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        True if all parameters are valid, False otherwise
    """
    missing_params = []
    
    if not args.uri:
        missing_params.append("URI (--uri or COSMOS_URI)")
    
    # Key is not required if using Managed Identity
    if not args.use_managed_identity and not args.key:
        missing_params.append("Key (--key or COSMOS_KEY) - or use --use-managed-identity")
    
    if not args.db:
        missing_params.append("Database (--db or COSMOS_DATABASE)")
    if not args.container:
        missing_params.append("Container (--container or COSMOS_CONTAINER)")
    
    if missing_params:
        logger.error(f"Missing required parameters: {', '.join(missing_params)}")
        return False
    
    return True


def main():
    """Main entry point for the Cosmos DB MCP server."""
    global cosmos_connection
    
    # Parse arguments
    args = parse_arguments()
    
    # Validate connection parameters
    if not validate_connection_params(args):
        sys.exit(1)
    
    # Initialize connection
    try:
        cosmos_connection = CosmosDBConnection(
            uri=args.uri,
            key=args.key,
            database=args.db,
            container=args.container,
            use_managed_identity=args.use_managed_identity
        )
        
        # Test connection
        auth_method = "Managed Identity" if args.use_managed_identity else "Access Key"
        logger.info(f"Connecting to Cosmos DB using {auth_method} - Database: {args.db}, Container: {args.container}")
        cosmos_connection.get_container_client()
        logger.info("Successfully connected to Cosmos DB")
        
    except Exception as e:
        logger.error(f"Failed to initialize Cosmos DB connection: {str(e)}")
        sys.exit(1)
    
    # Start MCP streamable-http server 
    try:
        logger.info(f"Starting Azure Cosmos DB MCP server on http://{args.host}:{args.port}/mcp")
        logger.info(f"Health check endpoint: http://{args.host}:{args.port}/health")
        mcp.run(transport="streamable-http", host=args.host, port=args.port)

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()