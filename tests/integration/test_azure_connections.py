"""Integration tests for Azure service connections."""

import os
from pathlib import Path

import pytest
from azure.core.exceptions import (
    ClientAuthenticationError, 
    ResourceNotFoundError,
    ServiceRequestError
)

from src.common.azure_clients import get_azure_clients, reset_azure_clients
from src.common.config import get_config, reset_config
from src.common.logging_config import get_logger

logger = get_logger(__name__)


@pytest.mark.integration
class TestAzureConnections:
    """Test Azure service connections with real services."""
    
    def setup_method(self):
        """Setup for each test."""
        reset_config()
        reset_azure_clients()
    
    def teardown_method(self):
        """Cleanup after each test."""
        reset_config()
        reset_azure_clients()
    
    def test_blob_storage_connection(self):
        """Test connection to Azure Blob Storage."""
        clients = get_azure_clients()
        
        try:
            # Try to list containers
            containers = list(clients.blob_service_client.list_containers())
            logger.info(f"Successfully connected to Blob Storage. Found {len(containers)} containers.")
            
            # Verify we can get container clients
            for container_type in ["raw_documents", "processed_documents", "embeddings"]:
                container_client = clients.get_container_client_by_type(container_type)
                assert container_client is not None
            
        except ClientAuthenticationError as e:
            pytest.skip(f"Authentication failed - check credentials: {e}")
        except Exception as e:
            pytest.fail(f"Failed to connect to Blob Storage: {e}")
    
    def test_blob_storage_container_operations(self):
        """Test container operations in Azure Blob Storage."""
        clients = get_azure_clients()
        config = get_config()
        
        try:
            # Test creating containers if they don't exist
            clients.create_containers_if_not_exists()
            
            # Verify all containers exist
            for container_type, container_name in config.storage.containers.items():
                container_client = clients.get_container_client(container_name)
                assert container_client.exists(), f"Container {container_name} should exist"
                logger.info(f"Container {container_name} exists")
            
        except ClientAuthenticationError as e:
            pytest.skip(f"Authentication failed - check credentials: {e}")
        except Exception as e:
            pytest.fail(f"Failed container operations: {e}")
    
    def test_cognitive_search_connection(self):
        """Test connection to Azure Cognitive Search."""
        clients = get_azure_clients()
        
        try:
            # Try to get service statistics
            stats = clients.search_index_client.get_service_statistics()
            logger.info(f"Successfully connected to Cognitive Search. Stats: {stats}")
            
            # Try to get search client
            search_client = clients.search_client
            assert search_client is not None
            
            # Try to get document count (index might not exist yet)
            try:
                count = search_client.get_document_count()
                logger.info(f"Document count in index: {count}")
            except ResourceNotFoundError:
                logger.info("Search index not found (expected for new setup)")
            
        except ClientAuthenticationError as e:
            pytest.skip(f"Authentication failed - check credentials: {e}")
        except ServiceRequestError as e:
            pytest.skip(f"Service not reachable - check endpoint: {e}")
        except Exception as e:
            pytest.fail(f"Failed to connect to Cognitive Search: {e}")
    
    def test_document_intelligence_connection(self):
        """Test connection to Azure Document Intelligence."""
        clients = get_azure_clients()
        
        try:
            # Try to list available models
            models = list(clients.document_analysis_client.list_document_models())
            logger.info(f"Successfully connected to Document Intelligence. Found {len(models)} models.")
            
            # Check if prebuilt-layout model is available
            model_ids = [model.model_id for model in models]
            assert "prebuilt-layout" in model_ids, "prebuilt-layout model should be available"
            
        except ClientAuthenticationError as e:
            pytest.skip(f"Authentication failed - check credentials: {e}")
        except ServiceRequestError as e:
            pytest.skip(f"Service not reachable - check endpoint: {e}")
        except Exception as e:
            pytest.fail(f"Failed to connect to Document Intelligence: {e}")
    
    def test_key_vault_connection(self):
        """Test connection to Azure Key Vault (if configured)."""
        config = get_config()
        
        if not config.settings.azure_key_vault_url:
            pytest.skip("Key Vault not configured")
        
        clients = get_azure_clients()
        
        try:
            # Try to list secrets
            secrets = list(clients.key_vault_client.list_properties_of_secrets())
            logger.info(f"Successfully connected to Key Vault. Found {len(secrets)} secrets.")
            
        except ClientAuthenticationError as e:
            pytest.skip(f"Authentication failed - check credentials: {e}")
        except Exception as e:
            pytest.fail(f"Failed to connect to Key Vault: {e}")
    
    def test_verify_all_connections(self):
        """Test verify_connections method."""
        clients = get_azure_clients()
        
        try:
            results = clients.verify_connections()
            
            logger.info("Connection verification results:")
            for service, status in results.items():
                if isinstance(status, bool):
                    logger.info(f"  {service}: {'Connected' if status else 'Failed'}")
                    if not status and f"{service}_error" in results:
                        logger.error(f"    Error: {results[f'{service}_error']}")
            
            # Check required services
            required_services = ["blob_storage", "cognitive_search", "document_intelligence"]
            failed_services = [s for s in required_services if not results.get(s, False)]
            
            if failed_services:
                pytest.fail(f"Failed to connect to required services: {failed_services}")
            
        except Exception as e:
            pytest.fail(f"Failed to verify connections: {e}")
    
    @pytest.mark.slow
    def test_blob_upload_download(self, sample_text_content):
        """Test uploading and downloading a blob."""
        clients = get_azure_clients()
        
        try:
            # Ensure container exists
            container_client = clients.get_container_client_by_type("raw_documents")
            if not container_client.exists():
                container_client.create_container()
            
            # Upload test blob
            blob_name = "test/integration_test.txt"
            blob_client = container_client.get_blob_client(blob_name)
            
            blob_client.upload_blob(
                sample_text_content.encode("utf-8"),
                overwrite=True
            )
            logger.info(f"Uploaded test blob: {blob_name}")
            
            # Download and verify
            downloaded = blob_client.download_blob().readall().decode("utf-8")
            assert downloaded == sample_text_content
            logger.info("Successfully downloaded and verified blob content")
            
            # Cleanup
            blob_client.delete_blob()
            logger.info("Cleaned up test blob")
            
        except ClientAuthenticationError as e:
            pytest.skip(f"Authentication failed - check credentials: {e}")
        except Exception as e:
            pytest.fail(f"Failed blob upload/download test: {e}")
    
    def test_environment_configuration(self):
        """Test that configuration is loaded correctly for the environment."""
        config = get_config()
        
        # Verify we're in test/development environment
        assert config.settings.environment in ["test", "development"]
        
        # Verify all required settings are present
        required_settings = [
            "azure_storage_connection_string",
            "azure_search_endpoint",
            "azure_document_intelligence_endpoint"
        ]
        
        for setting in required_settings:
            value = getattr(config.settings, setting, None)
            assert value is not None, f"Required setting {setting} is missing"
            assert value != "", f"Required setting {setting} is empty"
        
        logger.info("All required configuration settings are present")