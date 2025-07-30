"""Azure service client factory and management."""

from typing import Dict, Optional

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.keyvault.secrets import SecretClient

from .config import get_config


class AzureClients:
    """Factory for creating Azure service clients."""
    
    def __init__(self, config=None):
        """Initialize with configuration."""
        self.config = config or get_config()
        self._credential = None
        self._blob_service_client = None
        self._search_client = None
        self._search_index_client = None
        self._document_analysis_client = None
        self._key_vault_client = None
    
    @property
    def credential(self):
        """Get Azure credential for authentication."""
        if self._credential is None:
            settings = self.config.settings
            
            # Use client secret credential if available
            if all([
                settings.azure_tenant_id,
                settings.azure_client_id,
                settings.azure_client_secret
            ]):
                self._credential = ClientSecretCredential(
                    tenant_id=settings.azure_tenant_id,
                    client_id=settings.azure_client_id,
                    client_secret=settings.azure_client_secret
                )
            else:
                # Fall back to default credential (managed identity, Azure CLI, etc.)
                self._credential = DefaultAzureCredential()
        
        return self._credential
    
    @property
    def blob_service_client(self) -> BlobServiceClient:
        """Get or create Blob Service client."""
        if self._blob_service_client is None:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                self.config.settings.azure_storage_connection_string
            )
        return self._blob_service_client
    
    def get_container_client(self, container_name: str) -> ContainerClient:
        """Get container client by name."""
        return self.blob_service_client.get_container_client(container_name)
    
    def get_container_client_by_type(self, container_type: str) -> ContainerClient:
        """Get container client by type (raw_documents, processed_documents, etc.)."""
        container_name = self.config.get_storage_container(container_type)
        return self.get_container_client(container_name)
    
    @property
    def search_client(self) -> SearchClient:
        """Get or create Search client."""
        if self._search_client is None:
            self._search_client = SearchClient(
                endpoint=self.config.settings.azure_search_endpoint,
                index_name=self.config.settings.azure_search_index_name,
                credential=AzureKeyCredential(self.config.settings.azure_search_api_key)
            )
        return self._search_client
    
    @property
    def search_index_client(self) -> SearchIndexClient:
        """Get or create Search Index client for index management."""
        if self._search_index_client is None:
            self._search_index_client = SearchIndexClient(
                endpoint=self.config.settings.azure_search_endpoint,
                credential=AzureKeyCredential(self.config.settings.azure_search_api_key)
            )
        return self._search_index_client
    
    @property
    def document_analysis_client(self) -> DocumentAnalysisClient:
        """Get or create Document Analysis client."""
        if self._document_analysis_client is None:
            self._document_analysis_client = DocumentAnalysisClient(
                endpoint=self.config.settings.azure_document_intelligence_endpoint,
                credential=AzureKeyCredential(
                    self.config.settings.azure_document_intelligence_key
                )
            )
        return self._document_analysis_client
    
    @property
    def key_vault_client(self) -> Optional[SecretClient]:
        """Get or create Key Vault client (if configured)."""
        if self._key_vault_client is None and self.config.settings.azure_key_vault_url:
            self._key_vault_client = SecretClient(
                vault_url=self.config.settings.azure_key_vault_url,
                credential=self.credential
            )
        return self._key_vault_client
    
    def create_containers_if_not_exists(self) -> None:
        """Create all configured storage containers if they don't exist."""
        for container_type, container_name in self.config.storage.containers.items():
            container_client = self.get_container_client(container_name)
            if not container_client.exists():
                container_client.create_container()
                print(f"Created container: {container_name}")
            else:
                print(f"Container already exists: {container_name}")
    
    def verify_connections(self) -> Dict[str, bool]:
        """Verify connections to all Azure services."""
        results = {}
        
        # Test Blob Storage
        try:
            # List containers to verify connection
            containers = list(self.blob_service_client.list_containers())
            results["blob_storage"] = True
        except Exception as e:
            results["blob_storage"] = False
            results["blob_storage_error"] = str(e)
        
        # Test Cognitive Search
        try:
            # Get service statistics to verify connection
            self.search_index_client.get_service_statistics()
            results["cognitive_search"] = True
        except Exception as e:
            results["cognitive_search"] = False
            results["cognitive_search_error"] = str(e)
        
        # Test Document Intelligence
        try:
            # List models to verify connection
            models = list(self.document_analysis_client.list_document_models())
            results["document_intelligence"] = True
        except Exception as e:
            results["document_intelligence"] = False
            results["document_intelligence_error"] = str(e)
        
        # Test Key Vault (if configured)
        if self.config.settings.azure_key_vault_url:
            try:
                # List secrets to verify connection
                secrets = list(self.key_vault_client.list_properties_of_secrets())
                results["key_vault"] = True
            except Exception as e:
                results["key_vault"] = False
                results["key_vault_error"] = str(e)
        
        return results


# Global clients instance
_azure_clients: Optional[AzureClients] = None


def get_azure_clients() -> AzureClients:
    """Get or create Azure clients instance."""
    global _azure_clients
    if _azure_clients is None:
        _azure_clients = AzureClients()
    return _azure_clients


def reset_azure_clients() -> None:
    """Reset Azure clients (useful for testing)."""
    global _azure_clients
    _azure_clients = None