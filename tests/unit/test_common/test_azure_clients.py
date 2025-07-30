"""Unit tests for Azure client factory."""

from unittest.mock import Mock, patch, MagicMock, call

import pytest
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential, ClientSecretCredential

from src.common.azure_clients import (
    AzureClients, get_azure_clients, reset_azure_clients
)
from src.common.config import AppConfig


class TestAzureClients:
    """Test AzureClients class."""
    
    @pytest.mark.unit
    def test_initialization(self, test_config):
        """Test AzureClients initialization."""
        clients = AzureClients(config=test_config)
        
        assert clients.config == test_config
        assert clients._credential is None
        assert clients._blob_service_client is None
        assert clients._search_client is None
    
    @pytest.mark.unit
    def test_credential_with_service_principal(self, test_config, monkeypatch):
        """Test credential creation with service principal."""
        # Set service principal env vars
        monkeypatch.setenv("AZURE_TENANT_ID", "test-tenant")
        monkeypatch.setenv("AZURE_CLIENT_ID", "test-client")
        monkeypatch.setenv("AZURE_CLIENT_SECRET", "test-secret")
        
        # Recreate config to pick up new env vars
        test_config.settings.azure_tenant_id = "test-tenant"
        test_config.settings.azure_client_id = "test-client"
        test_config.settings.azure_client_secret = "test-secret"
        
        clients = AzureClients(config=test_config)
        
        with patch("src.common.azure_clients.ClientSecretCredential") as mock_cred:
            credential = clients.credential
            
            mock_cred.assert_called_once_with(
                tenant_id="test-tenant",
                client_id="test-client",
                client_secret="test-secret"
            )
    
    @pytest.mark.unit
    def test_credential_default(self, test_config):
        """Test credential creation with default credential."""
        # Ensure no service principal env vars
        test_config.settings.azure_tenant_id = None
        test_config.settings.azure_client_id = None
        test_config.settings.azure_client_secret = None
        
        clients = AzureClients(config=test_config)
        
        with patch("src.common.azure_clients.DefaultAzureCredential") as mock_cred:
            credential = clients.credential
            
            mock_cred.assert_called_once()
    
    @pytest.mark.unit
    def test_blob_service_client_creation(self, test_config):
        """Test blob service client creation."""
        clients = AzureClients(config=test_config)
        
        with patch("src.common.azure_clients.BlobServiceClient") as mock_blob:
            mock_instance = Mock()
            mock_blob.from_connection_string.return_value = mock_instance
            
            client = clients.blob_service_client
            
            mock_blob.from_connection_string.assert_called_once_with(
                test_config.settings.azure_storage_connection_string
            )
            assert client == mock_instance
            
            # Test singleton behavior
            client2 = clients.blob_service_client
            assert client2 == client
            assert mock_blob.from_connection_string.call_count == 1
    
    @pytest.mark.unit
    def test_get_container_client(self, test_config):
        """Test getting container client."""
        clients = AzureClients(config=test_config)
        
        mock_blob_client = Mock()
        mock_container_client = Mock()
        mock_blob_client.get_container_client.return_value = mock_container_client
        
        with patch.object(clients, "blob_service_client", mock_blob_client):
            container = clients.get_container_client("test-container")
            
            mock_blob_client.get_container_client.assert_called_once_with("test-container")
            assert container == mock_container_client
    
    @pytest.mark.unit
    def test_get_container_client_by_type(self, test_config):
        """Test getting container client by type."""
        clients = AzureClients(config=test_config)
        
        mock_blob_client = Mock()
        mock_container_client = Mock()
        mock_blob_client.get_container_client.return_value = mock_container_client
        
        with patch.object(clients, "blob_service_client", mock_blob_client):
            container = clients.get_container_client_by_type("raw_documents")
            
            # Should look up container name from config
            mock_blob_client.get_container_client.assert_called_once_with("test-raw-documents")
            assert container == mock_container_client
    
    @pytest.mark.unit
    def test_search_client_creation(self, test_config):
        """Test search client creation."""
        clients = AzureClients(config=test_config)
        
        with patch("src.common.azure_clients.SearchClient") as mock_search:
            mock_instance = Mock()
            mock_search.return_value = mock_instance
            
            client = clients.search_client
            
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args.kwargs["endpoint"] == test_config.settings.azure_search_endpoint
            assert call_args.kwargs["index_name"] == test_config.settings.azure_search_index_name
            assert isinstance(call_args.kwargs["credential"], AzureKeyCredential)
    
    @pytest.mark.unit
    def test_search_index_client_creation(self, test_config):
        """Test search index client creation."""
        clients = AzureClients(config=test_config)
        
        with patch("src.common.azure_clients.SearchIndexClient") as mock_search_index:
            mock_instance = Mock()
            mock_search_index.return_value = mock_instance
            
            client = clients.search_index_client
            
            mock_search_index.assert_called_once()
            call_args = mock_search_index.call_args
            assert call_args.kwargs["endpoint"] == test_config.settings.azure_search_endpoint
            assert isinstance(call_args.kwargs["credential"], AzureKeyCredential)
    
    @pytest.mark.unit
    def test_document_analysis_client_creation(self, test_config):
        """Test document analysis client creation."""
        clients = AzureClients(config=test_config)
        
        with patch("src.common.azure_clients.DocumentAnalysisClient") as mock_doc:
            mock_instance = Mock()
            mock_doc.return_value = mock_instance
            
            client = clients.document_analysis_client
            
            mock_doc.assert_called_once()
            call_args = mock_doc.call_args
            assert call_args.kwargs["endpoint"] == test_config.settings.azure_document_intelligence_endpoint
            assert isinstance(call_args.kwargs["credential"], AzureKeyCredential)
    
    @pytest.mark.unit
    def test_key_vault_client_creation(self, test_config):
        """Test key vault client creation."""
        test_config.settings.azure_key_vault_url = "https://test-vault.vault.azure.net/"
        clients = AzureClients(config=test_config)
        
        with patch("src.common.azure_clients.SecretClient") as mock_kv:
            mock_instance = Mock()
            mock_kv.return_value = mock_instance
            
            with patch.object(clients, "credential", Mock()):
                client = clients.key_vault_client
                
                mock_kv.assert_called_once()
                call_args = mock_kv.call_args
                assert call_args.kwargs["vault_url"] == test_config.settings.azure_key_vault_url
    
    @pytest.mark.unit
    def test_key_vault_client_not_configured(self, test_config):
        """Test key vault client when not configured."""
        test_config.settings.azure_key_vault_url = None
        clients = AzureClients(config=test_config)
        
        assert clients.key_vault_client is None
    
    @pytest.mark.unit
    def test_create_containers_if_not_exists(self, test_config):
        """Test container creation."""
        clients = AzureClients(config=test_config)
        
        mock_blob_client = Mock()
        mock_container_clients = {}
        
        # Create mock container clients
        for container_name in ["test-raw-documents", "test-processed-documents", "test-embeddings"]:
            mock_container = Mock()
            mock_container.exists.return_value = False
            mock_container.create_container = Mock()
            mock_container_clients[container_name] = mock_container
        
        mock_blob_client.get_container_client.side_effect = lambda name: mock_container_clients[name]
        
        with patch.object(clients, "blob_service_client", mock_blob_client):
            clients.create_containers_if_not_exists()
            
            # Verify all containers were checked and created
            for container_name, mock_container in mock_container_clients.items():
                mock_container.exists.assert_called_once()
                mock_container.create_container.assert_called_once()
    
    @pytest.mark.unit
    def test_verify_connections_all_success(self, test_config, mock_azure_clients):
        """Test verify_connections with all services working."""
        clients = AzureClients(config=test_config)
        
        # Mock successful responses
        mock_azure_clients["blob"].list_containers.return_value = []
        mock_azure_clients["search_index"].get_service_statistics.return_value = {"counters": {}}
        mock_azure_clients["document"].list_document_models.return_value = []
        
        results = clients.verify_connections()
        
        assert results["blob_storage"] is True
        assert results["cognitive_search"] is True
        assert results["document_intelligence"] is True
        assert "blob_storage_error" not in results
    
    @pytest.mark.unit
    def test_verify_connections_with_failures(self, test_config, mock_azure_clients):
        """Test verify_connections with some services failing."""
        clients = AzureClients(config=test_config)
        
        # Mock failures
        mock_azure_clients["blob"].list_containers.side_effect = Exception("Blob error")
        mock_azure_clients["search_index"].get_service_statistics.return_value = {"counters": {}}
        mock_azure_clients["document"].list_document_models.side_effect = Exception("Doc error")
        
        results = clients.verify_connections()
        
        assert results["blob_storage"] is False
        assert results["blob_storage_error"] == "Blob error"
        assert results["cognitive_search"] is True
        assert results["document_intelligence"] is False
        assert results["document_intelligence_error"] == "Doc error"


class TestAzureClientsSingleton:
    """Test Azure clients singleton pattern."""
    
    @pytest.mark.unit
    def test_get_azure_clients_singleton(self, mock_env):
        """Test get_azure_clients returns singleton instance."""
        reset_azure_clients()  # Ensure clean state
        
        clients1 = get_azure_clients()
        clients2 = get_azure_clients()
        
        assert clients1 is clients2
    
    @pytest.mark.unit
    def test_reset_azure_clients(self, mock_env):
        """Test reset_azure_clients clears singleton."""
        clients1 = get_azure_clients()
        reset_azure_clients()
        clients2 = get_azure_clients()
        
        assert clients1 is not clients2