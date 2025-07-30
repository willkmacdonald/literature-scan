"""Pytest configuration and fixtures for Medtech RAG tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch, MagicMock

import pytest
import yaml
from azure.core.credentials import AzureKeyCredential

from src.common.config import AppConfig, reset_config
from src.common.azure_clients import AzureClients, reset_azure_clients


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config_yaml(temp_dir: Path) -> Path:
    """Create a test configuration YAML file."""
    config_data = {
        "app": {
            "name": "Medtech RAG Test",
            "version": "0.1.0",
            "environment": "test",
            "debug": True
        },
        "storage": {
            "containers": {
                "raw_documents": "test-raw-documents",
                "processed_documents": "test-processed-documents",
                "embeddings": "test-embeddings"
            },
            "max_file_size_mb": 10,
            "allowed_extensions": [".pdf", ".txt"]
        },
        "search": {
            "index_name": "test-index",
            "api_version": "2023-11-01",
            "scoring_profile": "default",
            "max_results": 10,
            "highlight_fields": ["content"],
            "facets": ["author"]
        },
        "document_intelligence": {
            "api_version": "2023-07-31",
            "model_id": "prebuilt-layout",
            "features": ["tables"]
        },
        "embeddings": {
            "model_name": "test-model",
            "dimension": 384,
            "batch_size": 16,
            "max_length": 512
        },
        "chunking": {
            "strategy": "sliding_window",
            "chunk_size": 500,
            "chunk_overlap": 50,
            "min_chunk_size": 100
        },
        "retrieval": {
            "top_k": 5,
            "rerank_top_k": 3,
            "hybrid_alpha": 0.5,
            "min_relevance_score": 0.5
        },
        "logging": {
            "level": "DEBUG",
            "format": "json",
            "file": {
                "enabled": False
            }
        }
    }
    
    config_file = temp_dir / "test.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    
    return config_file


@pytest.fixture
def test_env_vars() -> Dict[str, str]:
    """Test environment variables."""
    return {
        "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=testkey;EndpointSuffix=core.windows.net",
        "AZURE_STORAGE_ACCOUNT_NAME": "testaccount",
        "AZURE_STORAGE_ACCOUNT_KEY": "testkey",
        "AZURE_SEARCH_ENDPOINT": "https://test.search.windows.net",
        "AZURE_SEARCH_API_KEY": "test-search-key",
        "AZURE_SEARCH_INDEX_NAME": "test-index",
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://test.cognitiveservices.azure.com/",
        "AZURE_DOCUMENT_INTELLIGENCE_KEY": "test-di-key",
        "LOG_LEVEL": "DEBUG",
        "ENVIRONMENT": "test",
        "API_PORT": "8001",
        "API_HOST": "127.0.0.1"
    }


@pytest.fixture
def mock_env(test_env_vars: Dict[str, str], monkeypatch):
    """Mock environment variables."""
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)
    yield
    # Clean up
    reset_config()
    reset_azure_clients()


@pytest.fixture
def test_config(test_config_yaml: Path, mock_env) -> AppConfig:
    """Create test configuration."""
    config = AppConfig(config_path=test_config_yaml)
    return config


@pytest.fixture
def mock_blob_service_client():
    """Mock Azure Blob Service Client."""
    mock_client = Mock()
    mock_container_client = Mock()
    
    # Mock container operations
    mock_container_client.exists.return_value = True
    mock_container_client.upload_blob = Mock()
    mock_container_client.list_blobs = Mock(return_value=[])
    
    # Mock service operations
    mock_client.get_container_client.return_value = mock_container_client
    mock_client.list_containers.return_value = []
    
    return mock_client


@pytest.fixture
def mock_search_client():
    """Mock Azure Search Client."""
    mock_client = Mock()
    
    # Mock search operations
    mock_client.search = Mock(return_value=[])
    mock_client.get_document_count = Mock(return_value=0)
    mock_client.upload_documents = Mock()
    
    return mock_client


@pytest.fixture
def mock_search_index_client():
    """Mock Azure Search Index Client."""
    mock_client = Mock()
    
    # Mock index operations
    mock_client.get_index = Mock()
    mock_client.create_or_update_index = Mock()
    mock_client.get_service_statistics = Mock(return_value={"counters": {}})
    
    return mock_client


@pytest.fixture
def mock_document_analysis_client():
    """Mock Azure Document Analysis Client."""
    mock_client = Mock()
    
    # Mock document operations
    mock_client.begin_analyze_document = Mock()
    mock_client.list_document_models = Mock(return_value=[])
    
    return mock_client


@pytest.fixture
def mock_azure_clients(
    mock_blob_service_client,
    mock_search_client,
    mock_search_index_client,
    mock_document_analysis_client
):
    """Mock all Azure clients."""
    with patch("src.common.azure_clients.BlobServiceClient") as blob_mock, \
         patch("src.common.azure_clients.SearchClient") as search_mock, \
         patch("src.common.azure_clients.SearchIndexClient") as search_index_mock, \
         patch("src.common.azure_clients.DocumentAnalysisClient") as doc_mock:
        
        blob_mock.from_connection_string.return_value = mock_blob_service_client
        search_mock.return_value = mock_search_client
        search_index_mock.return_value = mock_search_index_client
        doc_mock.return_value = mock_document_analysis_client
        
        yield {
            "blob": mock_blob_service_client,
            "search": mock_search_client,
            "search_index": mock_search_index_client,
            "document": mock_document_analysis_client
        }


@pytest.fixture
def sample_pdf_content() -> bytes:
    """Sample PDF content for testing."""
    # This is a minimal valid PDF
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n203\n%%EOF"


@pytest.fixture
def sample_text_content() -> str:
    """Sample text content for testing."""
    return """# Medical Research Paper

## Abstract
This is a sample medical research paper for testing purposes.

## Introduction
The introduction contains important information about the research topic.

## Methods
The methods section describes the research methodology.

## Results
The results section presents the findings.

## Conclusion
The conclusion summarizes the key findings."""


# Markers for test categorization
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests that don't require external services")
    config.addinivalue_line("markers", "integration: Integration tests that require Azure services")
    config.addinivalue_line("markers", "e2e: End-to-end tests for complete workflows")
    config.addinivalue_line("markers", "slow: Tests that take a long time to run")


# Skip integration tests if no Azure credentials
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip integration tests without credentials."""
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests"
    )