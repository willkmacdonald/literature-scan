"""Azure Blob Storage uploader for medical documents."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
import json

from azure.core.exceptions import AzureError
from azure.storage.blob import BlobClient, ContentSettings

from ..common.azure_clients import get_azure_clients
from ..common.config import get_config
from ..common.exceptions import StorageError
from ..common.logging_config import get_logger

logger = get_logger(__name__)


class MedicalDocumentUploader:
    """Upload and manage medical documents in Azure Blob Storage."""
    
    def __init__(self):
        """Initialize uploader with Azure clients."""
        self.clients = get_azure_clients()
        self.config = get_config()
    
    async def upload_document(
        self,
        file_path: Path,
        document_id: str,
        validation_result: Dict,
        metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Upload medical document to Azure Blob Storage.
        
        Args:
            file_path: Path to the PDF file
            document_id: Unique document identifier
            validation_result: Result from PDF validation
            metadata: Additional metadata to store
            
        Returns:
            Dict containing upload information
            
        Raises:
            StorageError: If upload fails
        """
        try:
            logger.info(f"Starting upload of document {document_id}")
            
            # Get container client for raw documents
            container_client = self.clients.get_container_client_by_type("raw_documents")
            
            # Ensure container exists
            if not container_client.exists():
                container_client.create_container()
                logger.info("Created raw-documents container")
            
            # Generate blob name with folder structure
            blob_name = self._generate_blob_name(document_id, file_path)
            
            # Prepare metadata
            blob_metadata = self._prepare_blob_metadata(
                document_id, validation_result, metadata
            )
            
            # Upload the PDF file
            pdf_blob_info = await self._upload_file(
                container_client, blob_name, file_path, blob_metadata
            )
            
            # Upload validation results as JSON
            validation_blob_info = await self._upload_validation_results(
                container_client, document_id, validation_result
            )
            
            upload_info = {
                "document_id": document_id,
                "pdf_blob_name": blob_name,
                "pdf_blob_url": pdf_blob_info["url"],
                "validation_blob_name": validation_blob_info["blob_name"],
                "validation_blob_url": validation_blob_info["url"],
                "upload_timestamp": datetime.utcnow().isoformat(),
                "container": "raw-documents"
            }
            
            logger.info(f"Successfully uploaded document {document_id}")
            return upload_info
            
        except Exception as e:
            logger.error(f"Failed to upload document {document_id}: {e}")
            raise StorageError(
                f"Document upload failed: {str(e)}",
                details={"document_id": document_id, "file_path": str(file_path)}
            )
    
    async def upload_processed_documents(
        self,
        document_id: str,
        markdown_content: str,
        json_metadata: Dict,
        processing_info: Dict
    ) -> Dict[str, str]:
        """
        Upload processed document outputs (markdown and JSON).
        
        Args:
            document_id: Document identifier
            markdown_content: Generated markdown content
            json_metadata: Extracted metadata
            processing_info: Processing details
            
        Returns:
            Upload information for processed documents
        """
        try:
            logger.info(f"Uploading processed documents for {document_id}")
            
            # Get container client for processed documents
            container_client = self.clients.get_container_client_by_type("processed_documents")
            
            # Ensure container exists
            if not container_client.exists():
                container_client.create_container()
                logger.info("Created processed-documents container")
            
            # Upload markdown file
            markdown_blob_name = f"{document_id}/{document_id}.md"
            markdown_info = await self._upload_content(
                container_client,
                markdown_blob_name,
                markdown_content,
                content_type="text/markdown",
                metadata={
                    "document_id": document_id,
                    "content_type": "markdown",
                    "processed_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Upload JSON metadata
            json_blob_name = f"{document_id}/{document_id}_metadata.json"
            json_info = await self._upload_content(
                container_client,
                json_blob_name,
                json.dumps(json_metadata, indent=2),
                content_type="application/json",
                metadata={
                    "document_id": document_id,
                    "content_type": "metadata",
                    "processed_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Upload processing info
            processing_blob_name = f"{document_id}/{document_id}_processing.json"
            processing_info_json = await self._upload_content(
                container_client,
                processing_blob_name,
                json.dumps(processing_info, indent=2),
                content_type="application/json",
                metadata={
                    "document_id": document_id,
                    "content_type": "processing_info",
                    "processed_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            upload_info = {
                "document_id": document_id,
                "markdown_blob_name": markdown_blob_name,
                "markdown_blob_url": markdown_info["url"],
                "metadata_blob_name": json_blob_name,
                "metadata_blob_url": json_info["url"],
                "processing_blob_name": processing_blob_name,
                "processing_blob_url": processing_info_json["url"],
                "upload_timestamp": datetime.utcnow().isoformat(),
                "container": "processed-documents"
            }
            
            logger.info(f"Successfully uploaded processed documents for {document_id}")
            return upload_info
            
        except Exception as e:
            logger.error(f"Failed to upload processed documents for {document_id}: {e}")
            raise StorageError(
                f"Processed document upload failed: {str(e)}",
                details={"document_id": document_id}
            )
    
    def list_documents(
        self,
        container_type: str = "raw_documents",
        prefix: Optional[str] = None
    ) -> List[Dict]:
        """
        List documents in specified container.
        
        Args:
            container_type: Type of container to list
            prefix: Optional prefix to filter blobs
            
        Returns:
            List of document information
        """
        try:
            container_client = self.clients.get_container_client_by_type(container_type)
            
            blobs = container_client.list_blobs(name_starts_with=prefix)
            
            documents = []
            for blob in blobs:
                doc_info = {
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                    "content_type": blob.content_settings.content_type if blob.content_settings else None,
                    "metadata": blob.metadata or {}
                }
                documents.append(doc_info)
            
            logger.info(f"Listed {len(documents)} documents from {container_type}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list documents from {container_type}: {e}")
            raise StorageError(f"Document listing failed: {str(e)}")
    
    def download_document(
        self,
        document_id: str,
        blob_name: str,
        container_type: str = "raw_documents"
    ) -> bytes:
        """
        Download document content.
        
        Args:
            document_id: Document identifier
            blob_name: Name of blob to download
            container_type: Container type
            
        Returns:
            Document content as bytes
        """
        try:
            container_client = self.clients.get_container_client_by_type(container_type)
            blob_client = container_client.get_blob_client(blob_name)
            
            content = blob_client.download_blob().readall()
            
            logger.info(f"Downloaded document {document_id} from {container_type}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to download document {document_id}: {e}")
            raise StorageError(f"Document download failed: {str(e)}")
    
    def delete_document(
        self,
        document_id: str,
        container_type: str = "raw_documents"
    ) -> bool:
        """
        Delete all blobs for a document.
        
        Args:
            document_id: Document identifier
            container_type: Container type
            
        Returns:
            True if successful
        """
        try:
            container_client = self.clients.get_container_client_by_type(container_type)
            
            # List all blobs with document_id prefix
            blobs = container_client.list_blobs(name_starts_with=document_id)
            
            deleted_count = 0
            for blob in blobs:
                blob_client = container_client.get_blob_client(blob.name)
                blob_client.delete_blob()
                deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} blobs for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise StorageError(f"Document deletion failed: {str(e)}")
    
    def _generate_blob_name(self, document_id: str, file_path: Path) -> str:
        """Generate structured blob name."""
        # Use folder structure: document_id/original_filename
        return f"{document_id}/{document_id}.pdf"
    
    def _prepare_blob_metadata(
        self,
        document_id: str,
        validation_result: Dict,
        additional_metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Prepare metadata for blob storage."""
        metadata = {
            "document_id": document_id,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "validation_status": validation_result.get("validation_status", "unknown"),
            "file_size": str(validation_result.get("basic_info", {}).get("file_size", 0)),
            "page_count": str(validation_result.get("pdf_info", {}).get("page_count", 0)),
            "is_medical": str(validation_result.get("medical_info", {}).get("is_medical_content", False)),
            "medical_score": str(validation_result.get("medical_info", {}).get("medical_score", 0))
        }
        
        # Add document type hints if available
        type_hints = validation_result.get("medical_info", {}).get("document_type_hints", [])
        if type_hints:
            metadata["document_types"] = ",".join(type_hints)
        
        # Add additional metadata
        if additional_metadata:
            for key, value in additional_metadata.items():
                # Azure metadata keys must be strings
                metadata[str(key)] = str(value)
        
        return metadata
    
    async def _upload_file(
        self,
        container_client,
        blob_name: str,
        file_path: Path,
        metadata: Dict[str, str]
    ) -> Dict[str, str]:
        """Upload file to blob storage."""
        try:
            blob_client = container_client.get_blob_client(blob_name)
            
            # Set content settings
            content_settings = ContentSettings(
                content_type="application/pdf",
                content_encoding=None,
                content_language=None,
                content_disposition=f'attachment; filename="{file_path.name}"'
            )
            
            # Upload file
            with open(file_path, "rb") as data:
                blob_client.upload_blob(
                    data,
                    overwrite=True,
                    metadata=metadata,
                    content_settings=content_settings
                )
            
            return {
                "blob_name": blob_name,
                "url": blob_client.url
            }
            
        except AzureError as e:
            raise StorageError(f"Azure upload failed: {str(e)}")
    
    async def _upload_content(
        self,
        container_client,
        blob_name: str,
        content: str,
        content_type: str,
        metadata: Dict[str, str]
    ) -> Dict[str, str]:
        """Upload string content to blob storage."""
        try:
            blob_client = container_client.get_blob_client(blob_name)
            
            content_settings = ContentSettings(content_type=content_type)
            
            blob_client.upload_blob(
                content,
                overwrite=True,
                metadata=metadata,
                content_settings=content_settings
            )
            
            return {
                "blob_name": blob_name,
                "url": blob_client.url
            }
            
        except AzureError as e:
            raise StorageError(f"Azure content upload failed: {str(e)}")
    
    async def _upload_validation_results(
        self,
        container_client,
        document_id: str,
        validation_result: Dict
    ) -> Dict[str, str]:
        """Upload validation results as JSON."""
        blob_name = f"{document_id}/{document_id}_validation.json"
        
        return await self._upload_content(
            container_client,
            blob_name,
            json.dumps(validation_result, indent=2),
            "application/json",
            {
                "document_id": document_id,
                "content_type": "validation_results",
                "upload_timestamp": datetime.utcnow().isoformat()
            }
        )


# Convenience functions
async def upload_medical_document(
    file_path: Path,
    document_id: str,
    validation_result: Dict,
    metadata: Optional[Dict] = None
) -> Dict[str, str]:
    """Upload a medical document to Azure Storage."""
    uploader = MedicalDocumentUploader()
    return await uploader.upload_document(file_path, document_id, validation_result, metadata)


def get_document_uploader() -> MedicalDocumentUploader:
    """Get document uploader instance."""
    return MedicalDocumentUploader()