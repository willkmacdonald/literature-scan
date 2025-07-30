"""Custom exceptions for Medtech RAG solution."""

from typing import Optional, Dict, Any


class MedtechRAGException(Exception):
    """Base exception for all Medtech RAG errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize with message and optional details."""
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(MedtechRAGException):
    """Raised when there's a configuration error."""
    pass


class AzureServiceError(MedtechRAGException):
    """Base exception for Azure service errors."""
    pass


class StorageError(AzureServiceError):
    """Raised when there's an Azure Storage error."""
    pass


class SearchError(AzureServiceError):
    """Raised when there's an Azure Cognitive Search error."""
    pass


class DocumentIntelligenceError(AzureServiceError):
    """Raised when there's an Azure Document Intelligence error."""
    pass


class KeyVaultError(AzureServiceError):
    """Raised when there's an Azure Key Vault error."""
    pass


class DocumentProcessingError(MedtechRAGException):
    """Raised when document processing fails."""
    pass


class ValidationError(MedtechRAGException):
    """Raised when validation fails."""
    pass


class FileValidationError(ValidationError):
    """Raised when file validation fails."""
    
    def __init__(self, message: str, filename: str, reason: str):
        """Initialize with file-specific details."""
        super().__init__(
            message,
            details={"filename": filename, "reason": reason}
        )
        self.filename = filename
        self.reason = reason


class ChunkingError(MedtechRAGException):
    """Raised when text chunking fails."""
    pass


class EmbeddingError(MedtechRAGException):
    """Raised when embedding generation fails."""
    pass


class RetrievalError(MedtechRAGException):
    """Raised when document retrieval fails."""
    pass


class APIError(MedtechRAGException):
    """Raised when API operations fail."""
    
    def __init__(self, message: str, status_code: int, details: Optional[Dict[str, Any]] = None):
        """Initialize with API-specific details."""
        super().__init__(message, details)
        self.status_code = status_code


class AuthenticationError(APIError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        """Initialize with 401 status code."""
        super().__init__(message, status_code=401)


class AuthorizationError(APIError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied"):
        """Initialize with 403 status code."""
        super().__init__(message, status_code=403)


class NotFoundError(APIError):
    """Raised when a resource is not found."""
    
    def __init__(self, message: str, resource_type: str, resource_id: str):
        """Initialize with 404 status code and resource details."""
        super().__init__(
            message,
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        """Initialize with 429 status code and retry information."""
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, status_code=429, details=details)
        self.retry_after = retry_after