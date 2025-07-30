"""Configuration management for Medtech RAG solution."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class StorageConfig(BaseModel):
    """Azure Storage configuration."""
    containers: Dict[str, str]
    max_file_size_mb: int = 50
    allowed_extensions: list[str] = [".pdf", ".docx", ".txt", ".md"]


class SearchConfig(BaseModel):
    """Azure Cognitive Search configuration."""
    index_name: str
    api_version: str = "2023-11-01"
    scoring_profile: str = "default"
    max_results: int = 50
    highlight_fields: list[str]
    facets: list[str]


class DocumentIntelligenceConfig(BaseModel):
    """Azure Document Intelligence configuration."""
    api_version: str = "2023-07-31"
    model_id: str = "prebuilt-layout"
    features: list[str]


class EmbeddingsConfig(BaseModel):
    """Embeddings configuration."""
    model_name: str
    dimension: int = 384
    batch_size: int = 32
    max_length: int = 512


class ChunkingConfig(BaseModel):
    """Text chunking configuration."""
    strategy: str = "sliding_window"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    separators: list[str] = ["\n\n", "\n", ". ", " "]

    @validator("chunk_overlap")
    def validate_overlap(cls, v: int, values: Dict[str, Any]) -> int:
        """Ensure overlap is less than chunk size."""
        chunk_size = values.get("chunk_size", 1000)
        if v >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v


class RetrievalConfig(BaseModel):
    """Retrieval configuration."""
    top_k: int = 10
    rerank_top_k: int = 5
    hybrid_alpha: float = 0.5
    min_relevance_score: float = 0.7

    @validator("hybrid_alpha")
    def validate_alpha(cls, v: float) -> float:
        """Ensure hybrid_alpha is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("hybrid_alpha must be between 0 and 1")
        return v


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Azure Storage
    azure_storage_connection_string: str
    azure_storage_account_name: str
    azure_storage_account_key: str
    
    # Azure Cognitive Search
    azure_search_endpoint: str
    azure_search_api_key: str
    azure_search_index_name: str
    
    # Azure Document Intelligence
    azure_document_intelligence_endpoint: str
    azure_document_intelligence_key: str
    
    # Azure Key Vault (Optional)
    azure_key_vault_url: Optional[str] = None
    
    # Azure Identity (for managed identity)
    azure_tenant_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_subscription_id: Optional[str] = None
    
    # Application Settings
    log_level: str = "INFO"
    environment: str = "development"
    api_port: int = 8000
    api_host: str = "0.0.0.0"

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


class AppConfig:
    """Main application configuration."""
    
    def __init__(self, config_path: Optional[Path] = None, env_path: Optional[Path] = None):
        """Initialize configuration from YAML and environment."""
        # Load environment variables
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()
        
        # Load settings from environment
        self.settings = Settings()
        
        # Determine config file path
        if config_path is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
            config_path = config_dir / f"{self.settings.environment}.yaml"
        
        # Load YAML configuration
        self.yaml_config = self._load_yaml(config_path)
        
        # Parse configuration sections
        self.storage = StorageConfig(**self.yaml_config.get("storage", {}))
        self.search = SearchConfig(**self.yaml_config.get("search", {}))
        self.document_intelligence = DocumentIntelligenceConfig(
            **self.yaml_config.get("document_intelligence", {})
        )
        self.embeddings = EmbeddingsConfig(**self.yaml_config.get("embeddings", {}))
        self.chunking = ChunkingConfig(**self.yaml_config.get("chunking", {}))
        self.retrieval = RetrievalConfig(**self.yaml_config.get("retrieval", {}))
    
    @staticmethod
    def _load_yaml(path: Path) -> Dict[str, Any]:
        """Load YAML configuration file."""
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path, "r") as f:
            return yaml.safe_load(f)
    
    def get_storage_container(self, container_type: str) -> str:
        """Get storage container name by type."""
        container = self.storage.containers.get(container_type)
        if not container:
            raise ValueError(f"Unknown container type: {container_type}")
        return container
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.settings.environment == "development"
    
    @property
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.settings.environment == "test"


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get or create configuration instance."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reset_config() -> None:
    """Reset configuration (useful for testing)."""
    global _config
    _config = None