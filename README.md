# Medtech RAG Solution

A Retrieval-Augmented Generation (RAG) solution for medical technology literature reviews, built on Azure services.

## Overview

This project provides a comprehensive solution for processing, storing, and retrieving medical literature using Azure's cloud services. It's designed to help researchers and medical professionals efficiently search through large volumes of medical documents.

## Architecture

The solution is built using a phased approach:

### Phase 1: Core Infrastructure (Completed)
- Configuration management
- Azure service clients
- Logging and error handling
- Comprehensive testing framework

### Phase 2: Document Processing (Upcoming)
- Document ingestion and validation
- PDF to Markdown conversion using Azure Document Intelligence
- Metadata extraction

### Phase 3: Chunking & Embeddings (Upcoming)
- Intelligent text chunking
- Medical domain-specific embeddings
- Batch processing pipeline

### Phase 4: Vector Store & Retrieval (Upcoming)
- Azure Cognitive Search integration
- Hybrid search (keyword + semantic)
- Result reranking

### Phase 5: API & Web Interface (Upcoming)
- FastAPI backend
- Document upload and search endpoints
- Simple web interface

## Prerequisites

- Python 3.9+
- Azure subscription
- Azure CLI installed and configured

## Quick Start

### 1. Clone the repository
```bash
git clone <repository-url>
cd medtech-rag
```

### 2. Set up Python environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up Azure resources
```bash
# Login to Azure
az login

# Run the setup script
python scripts/setup_azure_resources.py
```

This script will create:
- Resource group
- Storage account with containers
- Cognitive Search service (Free tier)
- Document Intelligence service (Free tier)
- Key Vault (optional)

### 4. Configure environment
The setup script creates a `.env` file. Review and update if needed:
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

### 5. Run tests
```bash
# Run unit tests
pytest -m unit

# Run integration tests (requires Azure setup)
pytest -m integration --run-integration

# Run all tests with coverage
pytest --cov=src --cov-report=html
```

## Project Structure

```
medtech-rag/
├── src/
│   └── common/              # Phase 1: Core infrastructure
│       ├── config.py        # Configuration management
│       ├── azure_clients.py # Azure service clients
│       ├── logging_config.py # Structured logging
│       └── exceptions.py    # Custom exceptions
├── tests/
│   ├── unit/               # Unit tests (no Azure required)
│   ├── integration/        # Integration tests (Azure required)
│   └── e2e/               # End-to-end tests
├── scripts/
│   └── setup_azure_resources.py  # Azure setup automation
├── config/
│   └── development.yaml    # Development configuration
└── requirements.txt        # Production dependencies
```

## Configuration

The application uses a two-tier configuration system:

1. **Environment Variables** (`.env` file)
   - Azure connection strings and keys
   - Runtime settings

2. **YAML Configuration** (`config/development.yaml`)
   - Application settings
   - Feature configuration
   - Processing parameters

## Testing

The project includes comprehensive testing:

- **Unit Tests**: Test individual components without external dependencies
- **Integration Tests**: Test Azure service connections
- **E2E Tests**: Test complete workflows (added per phase)

Run tests with markers:
```bash
pytest -m unit          # Fast, no Azure needed
pytest -m integration   # Requires Azure services
pytest -m e2e          # Full workflow tests
```

## Development

### Code Quality
```bash
# Format code
black src tests

# Lint code
ruff src tests

# Type checking
mypy src
```

### Adding New Features
1. Create feature branch
2. Implement with tests
3. Ensure all tests pass
4. Update documentation

## Azure Services Used

- **Azure Blob Storage**: Document storage
- **Azure Cognitive Search**: Vector search and retrieval
- **Azure Document Intelligence**: PDF processing
- **Azure Key Vault**: Secrets management (optional)

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure Azure CLI is logged in: `az login`
   - Check .env file has correct credentials

2. **Missing Dependencies**
   - Install dependencies: `pip install -r requirements.txt`

3. **Test Failures**
   - For integration tests, ensure Azure resources exist
   - Check .env file is properly configured

## Next Steps

After Phase 1 setup:
1. Verify all tests pass
2. Review Azure resources in portal
3. Proceed to Phase 2 implementation

## Contributing

This is a training project. Feel free to experiment and extend!

## License

This project is for educational purposes.