# Medtech Literature Scan

An advanced RAG (Retrieval-Augmented Generation) solution designed specifically for medical technology professionals to efficiently search and analyze medical literature. Built on Azure services with specialized medical embeddings and intelligent document processing.

## Overview

This solution is optimized for **medtech companies** where experts need to find specific facts, regulatory precedents, and clinical evidence from medical literature. It uses:

- **S-PubMedBert-MS-MARCO embeddings** for precise medical Q&A retrieval
- **Hierarchical document processing** that preserves tables and figures
- **Anthropic's contextual retrieval** adapted for medical content
- **LLM-powered table summarization** for large clinical data tables
- **Rich metadata extraction** for advanced filtering and ranking

## Key Features for Medtech Professionals

### 🔍 **Specialized Medical Search**
- **Q&A Optimized**: Find specific facts like "30-day mortality rates for Device X"
- **Regulatory Focus**: Search FDA 510(k)s, PMA studies, and clinical trial endpoints
- **Statistical Precision**: Locate p-values, confidence intervals, and sample sizes

### 📊 **Intelligent Table Handling**
- **Smart Summarization**: Large clinical tables summarized by GPT-4 for searchability
- **Preserved Structure**: Small tables kept whole for complete data access
- **Metadata Rich**: Every table tagged with type, patient demographics, statistical content

### 🧠 **Medical-Aware Processing**
- **Document Classification**: Automatically identifies clinical trials, FDA guidance, journal articles
- **Section Preservation**: Maintains Methods → Results → Discussion structure
- **Contextual Chunking**: Adds medical context to each chunk for better retrieval

### 🎯 **Advanced Filtering & Ranking**
- **Pre-query Filtering**: Device class, regulatory pathway, study type, publication date
- **Metadata-Enhanced Scoring**: Boosts results based on statistical significance, sample size, journal impact
- **Role-Based Personalization**: Different weights for regulatory affairs vs clinical research teams

## Architecture

### Phase 1: Core Infrastructure ✅ **COMPLETED**
- Medical-focused configuration with S-PubMedBert-MS-MARCO settings  
- Azure service clients with storage organization
- Comprehensive PDF validation for medical documents
- Structured logging and error handling

### Phase 2A: Document Processing Foundation ✅ **COMPLETED**
- Medical PDF validator with regulatory keyword detection
- Azure Blob Storage with hierarchical document organization
- Rich metadata extraction and preservation
- Document type classification (clinical trials, FDA guidance, etc.)

### Phase 2B: Document Intelligence (In Progress)
- Azure Document Intelligence integration for PDF → structured data
- Medical-optimized markdown generation with section markers
- Table extraction and intelligent size-based handling
- Enhanced metadata extraction (authors, DOIs, study details)

### Phase 3: Advanced Chunking & Context
- **Hierarchical Medical Chunker**: Respects document structure
- **Smart Table Handler**: LLM summarization for large tables
- **Contextual Enhancement**: Anthropic's approach adapted for medical content
- **S-PubMedBert-MS-MARCO**: 768-dimensional medical embeddings

### Phase 4: Intelligent Retrieval
- **Hybrid Search**: BM25 + semantic search with medical boosting
- **Metadata-Enhanced Ranking**: Quality scores, statistical significance, recency
- **Faceted Results**: Filter by device class, study type, statistical content
- **Role-Based Personalization**: Regulatory vs clinical vs product management views

### Phase 5: Professional Interface
- **Expert Search UI**: Advanced filtering and faceted browsing
- **Result Contextualization**: Show full tables, related figures, cross-references  
- **Export Capabilities**: Evidence packages for regulatory submissions
- **Integration APIs**: Connect with existing medtech workflows

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
│   ├── common/              # Core infrastructure
│   │   ├── config.py        # Configuration management
│   │   ├── azure_clients.py # Azure service clients
│   │   ├── logging_config.py # Structured logging
│   │   └── exceptions.py    # Custom exceptions
│   ├── document_ingestion/  # Phase 2A: Document processing
│   │   ├── pdf_validator.py # Medical PDF validation
│   │   └── blob_uploader.py # Azure Storage with metadata
│   ├── document_intelligence/ # Phase 2B: Azure Document Intelligence
│   │   ├── pdf_analyzer.py   # PDF → structured data
│   │   ├── markdown_generator.py # Medical markdown output
│   │   └── metadata_extractor.py # Enhanced metadata
│   ├── chunking/           # Phase 3: Advanced chunking
│   │   ├── medical_chunker.py    # Hierarchical chunking
│   │   ├── table_handler.py      # Smart table processing
│   │   └── context_generator.py  # LLM-powered context
│   └── embeddings/         # Phase 3: Medical embeddings
│       ├── pubmed_embedder.py    # S-PubMedBert-MS-MARCO
│       └── batch_processor.py    # Efficient processing
├── tests/
│   ├── unit/               # Comprehensive unit tests
│   ├── integration/        # Azure service tests
│   └── e2e/               # Full pipeline tests
├── scripts/
│   └── setup_azure_resources.py  # Automated Azure setup
├── config/
│   └── development.yaml    # Medical-focused configuration
└── requirements.txt        # All dependencies
```

## Configuration

### Medical-Optimized Settings

The system is configured specifically for medical literature processing:

**Embeddings (S-PubMedBert-MS-MARCO)**:
```yaml
embeddings:
  model_name: "pritamdeka/S-PubMedBert-MS-MARCO"
  dimension: 768                 # High-quality medical embeddings
  max_length: 350               # Model's token limit
  batch_size: 16                # Optimized for 768-dim vectors
```

**Hierarchical Chunking**:
```yaml
chunking:
  strategy: "contextual_medical"
  base_chunk_size: 300          # Fits in 350 tokens with context
  preserve_medical_sections: true
  context_tokens: 75            # Anthropic's contextual addition
  separators:                   # Medical document structure
    - "\n## "                  # Section headers
    - "\n### "                 # Subsections  
    - "[TABLE_END]"            # Table boundaries
```

**Document Intelligence**:
```yaml
document_intelligence:
  medical_focus: true
  extract_tables: true          # Critical for clinical data
  extract_figures: true         # Preserve figure references
  confidence_threshold: 0.85    # High accuracy for medical content
```

**Contextual Retrieval**:
```yaml
contextual_retrieval:
  enabled: true
  context_model: "claude-3-haiku-20240307"  # Fast, cost-effective
  hybrid_search: true                       # BM25 + semantic
  medical_context: true                     # Medical-aware context
```

### Configuration Files

1. **Environment Variables** (`.env` file)
   - Azure connection strings and API keys
   - OpenAI/Claude API keys for LLM summarization
   - Runtime settings

2. **YAML Configuration** (`config/development.yaml`)
   - Medical processing parameters
   - Embedding and chunking settings
   - Quality thresholds and filtering rules

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

## Technology Stack

### Azure Services
- **Azure Blob Storage**: Hierarchical document organization with rich metadata
- **Azure Cognitive Search**: Hybrid search (BM25 + semantic) with medical boosting
- **Azure Document Intelligence**: PDF → structured data with table/figure extraction
- **Azure Key Vault**: Secure credential management (optional)

### AI/ML Models  
- **S-PubMedBert-MS-MARCO**: 768-dimensional medical embeddings optimized for Q&A retrieval
- **Claude-3-Haiku**: Fast context generation for Anthropic's contextual retrieval
- **GPT-4-Turbo**: Table summarization for large clinical data tables
- **Azure OpenAI**: Alternative LLM option for table processing

### Key Dependencies
- **sentence-transformers**: S-PubMedBert-MS-MARCO integration
- **anthropic**: Claude API for contextual enhancement  
- **openai**: GPT-4 for table summarization
- **pypdf + pymupdf**: Advanced PDF processing and validation
- **python-magic**: File type validation

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

## Use Cases

### For Regulatory Affairs Teams
- **510(k) Precedent Search**: "Find similar devices with XYZ indication approved in last 5 years"
- **Endpoint Analysis**: "What primary endpoints were used for cardiac stent studies?"
- **Safety Data**: "Comparison of adverse event rates across competitive devices"

### For Clinical Research Teams  
- **Study Design**: "Sample sizes and statistical methods for non-inferiority trials"
- **Patient Population**: "Inclusion/exclusion criteria for heart failure device studies"
- **Outcome Measures**: "30-day, 6-month, and 1-year follow-up protocols"

### For Product Management
- **Market Analysis**: "Clinical outcomes and health economics data for competitor devices"
- **Evidence Gaps**: "Areas lacking sufficient clinical evidence for our therapeutic area"
- **Publication Strategy**: "High-impact journals and successful publication patterns"

## Current Status

- ✅ **Phase 1**: Core infrastructure with Azure integration
- ✅ **Phase 2A**: Medical PDF validation and storage with metadata
- 🔄 **Phase 2B**: Document Intelligence integration (in progress)
- ⏳ **Phase 3**: Advanced chunking with LLM enhancement
- ⏳ **Phase 4**: Intelligent retrieval with medical boosting
- ⏳ **Phase 5**: Professional search interface

## Contributing

This is a training project focused on medical technology literature analysis. Key areas for extension:
- Additional medical document types (FDA guidance, patents, etc.)
- Integration with regulatory databases (FDA 510(k), clinical trials.gov)  
- Advanced analytics (citation networks, trend analysis)
- Multi-language support for international regulations

## License

This project is for educational and training purposes.