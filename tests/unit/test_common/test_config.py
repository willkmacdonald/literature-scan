"""Unit tests for configuration management."""

import os
from pathlib import Path
from unittest.mock import patch, Mock

import pytest
import yaml

from src.common.config import (
    AppConfig, Settings, StorageConfig, SearchConfig,
    ChunkingConfig, RetrievalConfig, get_config, reset_config
)


class TestSettings:
    """Test Settings class."""
    
    @pytest.mark.unit
    def test_settings_from_env(self, mock_env):
        """Test loading settings from environment variables."""
        settings = Settings()
        
        assert settings.azure_storage_connection_string == "DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=testkey;EndpointSuffix=core.windows.net"
        assert settings.azure_storage_account_name == "testaccount"
        assert settings.azure_search_endpoint == "https://test.search.windows.net"
        assert settings.log_level == "DEBUG"
        assert settings.environment == "test"
        assert settings.api_port == 8001
    
    @pytest.mark.unit
    def test_settings_defaults(self, mock_env):
        """Test default settings values."""
        # Remove some env vars to test defaults
        if "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]
        
        settings = Settings()
        assert settings.log_level == "INFO"  # Default value
        assert settings.azure_key_vault_url is None  # Optional field


class TestStorageConfig:
    """Test StorageConfig class."""
    
    @pytest.mark.unit
    def test_storage_config_valid(self):
        """Test valid storage configuration."""
        config = StorageConfig(
            containers={
                "raw_documents": "raw",
                "processed_documents": "processed"
            },
            max_file_size_mb=50,
            allowed_extensions=[".pdf", ".txt"]
        )
        
        assert config.max_file_size_mb == 50
        assert ".pdf" in config.allowed_extensions
        assert len(config.containers) == 2
    
    @pytest.mark.unit
    def test_storage_config_defaults(self):
        """Test storage configuration defaults."""
        config = StorageConfig(containers={"test": "test-container"})
        
        assert config.max_file_size_mb == 50  # Default
        assert ".pdf" in config.allowed_extensions  # Default list


class TestChunkingConfig:
    """Test ChunkingConfig class."""
    
    @pytest.mark.unit
    def test_chunking_config_valid(self):
        """Test valid chunking configuration."""
        config = ChunkingConfig(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.strategy == "sliding_window"  # Default
    
    @pytest.mark.unit
    def test_chunking_config_invalid_overlap(self):
        """Test chunking configuration with invalid overlap."""
        with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
            ChunkingConfig(
                chunk_size=100,
                chunk_overlap=150  # Greater than chunk_size
            )


class TestRetrievalConfig:
    """Test RetrievalConfig class."""
    
    @pytest.mark.unit
    def test_retrieval_config_valid(self):
        """Test valid retrieval configuration."""
        config = RetrievalConfig(
            top_k=10,
            hybrid_alpha=0.7
        )
        
        assert config.top_k == 10
        assert config.hybrid_alpha == 0.7
    
    @pytest.mark.unit
    def test_retrieval_config_invalid_alpha(self):
        """Test retrieval configuration with invalid alpha."""
        with pytest.raises(ValueError, match="hybrid_alpha must be between 0 and 1"):
            RetrievalConfig(hybrid_alpha=1.5)
        
        with pytest.raises(ValueError, match="hybrid_alpha must be between 0 and 1"):
            RetrievalConfig(hybrid_alpha=-0.1)


class TestAppConfig:
    """Test AppConfig class."""
    
    @pytest.mark.unit
    def test_app_config_initialization(self, test_config_yaml, mock_env):
        """Test AppConfig initialization."""
        config = AppConfig(config_path=test_config_yaml)
        
        # Check settings loaded from environment
        assert config.settings.environment == "test"
        assert config.settings.log_level == "DEBUG"
        
        # Check YAML config loaded
        assert config.storage.containers["raw_documents"] == "test-raw-documents"
        assert config.search.index_name == "test-index"
        assert config.embeddings.model_name == "test-model"
    
    @pytest.mark.unit
    def test_app_config_missing_file(self, temp_dir, mock_env):
        """Test AppConfig with missing configuration file."""
        with pytest.raises(FileNotFoundError):
            AppConfig(config_path=temp_dir / "nonexistent.yaml")
    
    @pytest.mark.unit
    def test_get_storage_container(self, test_config):
        """Test getting storage container by type."""
        container = test_config.get_storage_container("raw_documents")
        assert container == "test-raw-documents"
        
        # Test invalid container type
        with pytest.raises(ValueError, match="Unknown container type"):
            test_config.get_storage_container("invalid_type")
    
    @pytest.mark.unit
    def test_environment_checks(self, test_config):
        """Test environment check properties."""
        assert test_config.is_test is True
        assert test_config.is_development is False
    
    @pytest.mark.unit
    def test_yaml_structure_validation(self, temp_dir, mock_env):
        """Test YAML configuration structure validation."""
        # Create invalid YAML
        invalid_config = temp_dir / "invalid.yaml"
        with open(invalid_config, "w") as f:
            yaml.dump({
                "chunking": {
                    "chunk_size": 100,
                    "chunk_overlap": 200  # Invalid: overlap > size
                }
            }, f)
        
        with pytest.raises(ValueError):
            AppConfig(config_path=invalid_config)


class TestConfigSingleton:
    """Test configuration singleton pattern."""
    
    @pytest.mark.unit
    def test_get_config_singleton(self, test_config_yaml, mock_env):
        """Test get_config returns singleton instance."""
        reset_config()  # Ensure clean state
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    @pytest.mark.unit
    def test_reset_config(self, mock_env):
        """Test reset_config clears singleton."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        
        assert config1 is not config2


class TestConfigIntegration:
    """Test configuration integration scenarios."""
    
    @pytest.mark.unit
    def test_partial_yaml_config(self, temp_dir, mock_env):
        """Test loading partial YAML configuration."""
        # Create minimal YAML
        minimal_config = temp_dir / "minimal.yaml"
        with open(minimal_config, "w") as f:
            yaml.dump({
                "storage": {
                    "containers": {"raw_documents": "raw"}
                },
                "search": {
                    "index_name": "minimal-index",
                    "highlight_fields": ["content"],
                    "facets": []
                }
            }, f)
        
        config = AppConfig(config_path=minimal_config)
        
        # Should load with defaults for missing sections
        assert config.storage.containers["raw_documents"] == "raw"
        assert config.chunking.chunk_size == 1000  # Default
    
    @pytest.mark.unit
    def test_env_override(self, test_config_yaml, monkeypatch):
        """Test environment variables override YAML config."""
        # Set different index name in env
        monkeypatch.setenv("AZURE_SEARCH_INDEX_NAME", "env-override-index")
        
        config = AppConfig(config_path=test_config_yaml)
        
        # Env var should override YAML
        assert config.settings.azure_search_index_name == "env-override-index"
        # But YAML config should still be loaded
        assert config.search.index_name == "test-index"