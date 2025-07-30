"""PDF validation for medical documents."""

import hashlib
import magic
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid

import fitz  # PyMuPDF
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ..common.config import get_config
from ..common.exceptions import FileValidationError, ValidationError
from ..common.logging_config import get_logger

logger = get_logger(__name__)


class MedicalPDFValidator:
    """Validator for medical PDF documents with enhanced validation."""
    
    def __init__(self):
        """Initialize validator with configuration."""
        self.config = get_config()
        self.max_file_size = self.config.storage.max_file_size_mb * 1024 * 1024
        
        # Medical document indicators
        self.medical_keywords = [
            "clinical", "medical", "patient", "treatment", "diagnosis",
            "therapeutic", "pharmaceutical", "fda", "trial", "study",
            "bmj", "nejm", "pubmed", "medline", "clinical trial",
            "randomized", "systematic review", "meta-analysis",
            "medical device", "drug", "therapy", "intervention"
        ]
        
        # Regulatory document indicators
        self.regulatory_keywords = [
            "510(k)", "pma", "premarket", "fda guidance", "ce mark",
            "regulatory", "submission", "clearance", "approval",
            "device classification", "quality system", "gmp", "gcp"
        ]
    
    def validate_file(self, file_path: Path) -> Dict[str, any]:
        """
        Comprehensive validation of medical PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dict containing validation results and metadata
            
        Raises:
            FileValidationError: If validation fails
        """
        try:
            logger.info(f"Starting validation of {file_path}")
            
            # Basic file validation
            basic_info = self._validate_basic_file(file_path)
            
            # PDF-specific validation
            pdf_info = self._validate_pdf_structure(file_path)
            
            # Medical content validation
            medical_info = self._validate_medical_content(file_path)
            
            # Generate document ID
            document_id = self._generate_document_id(file_path)
            
            validation_result = {
                "document_id": document_id,
                "file_path": str(file_path),
                "validation_status": "passed",
                "basic_info": basic_info,
                "pdf_info": pdf_info,
                "medical_info": medical_info,
                "validation_errors": []
            }
            
            logger.info(f"Validation passed for {file_path}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Validation failed for {file_path}: {e}")
            raise FileValidationError(
                f"PDF validation failed: {str(e)}",
                filename=str(file_path),
                reason=str(e)
            )
    
    def _validate_basic_file(self, file_path: Path) -> Dict[str, any]:
        """Validate basic file properties."""
        if not file_path.exists():
            raise FileValidationError(
                "File does not exist",
                filename=str(file_path),
                reason="File not found"
            )
        
        # Check file extension
        if file_path.suffix.lower() != '.pdf':
            raise FileValidationError(
                "Invalid file extension",
                filename=str(file_path),
                reason=f"Expected .pdf, got {file_path.suffix}"
            )
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise FileValidationError(
                "File too large",
                filename=str(file_path),
                reason=f"Size {file_size} bytes exceeds limit {self.max_file_size} bytes"
            )
        
        if file_size == 0:
            raise FileValidationError(
                "Empty file",
                filename=str(file_path),
                reason="File size is 0 bytes"
            )
        
        # Check MIME type
        mime_type = magic.from_file(str(file_path), mime=True)
        if mime_type != 'application/pdf':
            raise FileValidationError(
                "Invalid MIME type",
                filename=str(file_path),
                reason=f"Expected application/pdf, got {mime_type}"
            )
        
        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        
        return {
            "file_size": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "mime_type": mime_type,
            "file_hash": file_hash,
            "filename": file_path.name
        }
    
    def _validate_pdf_structure(self, file_path: Path) -> Dict[str, any]:
        """Validate PDF structure and extract metadata."""
        try:
            # Use PyPDF for basic validation
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                
                if reader.is_encrypted:
                    raise FileValidationError(
                        "Encrypted PDF not supported",
                        filename=str(file_path),
                        reason="PDF is password protected"
                    )
                
                page_count = len(reader.pages)
                
                # Extract PDF metadata
                metadata = reader.metadata or {}
                pdf_title = metadata.get('/Title', '')
                pdf_author = metadata.get('/Author', '')
                pdf_subject = metadata.get('/Subject', '')
                pdf_creator = metadata.get('/Creator', '')
                pdf_producer = metadata.get('/Producer', '')
                
                # Use PyMuPDF for more detailed analysis
                doc = fitz.open(str(file_path))
                
                # Check for text content
                has_text = False
                has_images = False
                has_tables = False  # Basic heuristic
                total_chars = 0
                
                for page_num in range(min(3, page_count)):  # Check first 3 pages
                    page = doc[page_num]
                    text = page.get_text()
                    
                    if text.strip():
                        has_text = True
                        total_chars += len(text)
                    
                    # Check for images
                    if page.get_images():
                        has_images = True
                    
                    # Basic table detection (look for table-like patterns)
                    if self._detect_table_patterns(text):
                        has_tables = True
                
                doc.close()
                
                if not has_text:
                    raise FileValidationError(
                        "No extractable text found",
                        filename=str(file_path),
                        reason="PDF appears to be image-only or corrupted"
                    )
                
                return {
                    "page_count": page_count,
                    "has_text": has_text,
                    "has_images": has_images,
                    "has_tables": has_tables,
                    "total_characters": total_chars,
                    "avg_chars_per_page": total_chars // max(1, min(3, page_count)),
                    "pdf_metadata": {
                        "title": pdf_title,
                        "author": pdf_author,
                        "subject": pdf_subject,
                        "creator": pdf_creator,
                        "producer": pdf_producer
                    }
                }
                
        except PdfReadError as e:
            raise FileValidationError(
                "Corrupted PDF file",
                filename=str(file_path),
                reason=f"PDF reading error: {str(e)}"
            )
        except Exception as e:
            raise FileValidationError(
                "PDF validation failed",
                filename=str(file_path),
                reason=f"Unexpected error: {str(e)}"
            )
    
    def _validate_medical_content(self, file_path: Path) -> Dict[str, any]:
        """Validate and analyze medical content indicators."""
        try:
            doc = fitz.open(str(file_path))
            
            # Sample text from first few pages
            sample_text = ""
            for page_num in range(min(5, len(doc))):  # First 5 pages
                page = doc[page_num]
                sample_text += page.get_text().lower()
            
            doc.close()
            
            # Count medical keywords
            medical_score = 0
            found_medical_keywords = []
            for keyword in self.medical_keywords:
                if keyword.lower() in sample_text:
                    medical_score += sample_text.count(keyword.lower())
                    found_medical_keywords.append(keyword)
            
            # Count regulatory keywords
            regulatory_score = 0
            found_regulatory_keywords = []
            for keyword in self.regulatory_keywords:
                if keyword.lower() in sample_text:
                    regulatory_score += sample_text.count(keyword.lower())
                    found_regulatory_keywords.append(keyword)
            
            # Determine document type hints
            document_type_hints = []
            if "clinical trial" in sample_text or "randomized" in sample_text:
                document_type_hints.append("clinical_trial")
            if "fda" in sample_text or "510(k)" in sample_text or "pma" in sample_text:
                document_type_hints.append("regulatory")
            if "bmj" in sample_text or "nejm" in sample_text:
                document_type_hints.append("journal_article")
            if "systematic review" in sample_text or "meta-analysis" in sample_text:
                document_type_hints.append("review")
            
            # Check if this appears to be medical content
            is_medical = medical_score > 0 or regulatory_score > 0
            
            if not is_medical:
                logger.warning(f"Document {file_path} does not appear to be medical content")
            
            return {
                "is_medical_content": is_medical,
                "medical_score": medical_score,
                "regulatory_score": regulatory_score,
                "found_medical_keywords": found_medical_keywords[:10],  # Limit output
                "found_regulatory_keywords": found_regulatory_keywords[:10],
                "document_type_hints": document_type_hints,
                "sample_length": len(sample_text)
            }
            
        except Exception as e:
            logger.warning(f"Medical content validation failed for {file_path}: {e}")
            return {
                "is_medical_content": None,
                "medical_score": 0,
                "regulatory_score": 0,
                "found_medical_keywords": [],
                "found_regulatory_keywords": [],
                "document_type_hints": [],
                "validation_error": str(e)
            }
    
    def _detect_table_patterns(self, text: str) -> bool:
        """Basic heuristic to detect table-like content."""
        lines = text.split('\n')
        
        # Look for lines with multiple tabs or multiple spaces
        table_like_lines = 0
        for line in lines:
            if line.count('\t') >= 2 or len([x for x in line.split() if len(x) > 0]) >= 4:
                table_like_lines += 1
        
        # If more than 10% of lines look table-like, assume tables present
        return table_like_lines > len(lines) * 0.1
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _generate_document_id(self, file_path: Path) -> str:
        """Generate unique document ID."""
        # Use a combination of filename and hash for uniqueness
        base_id = f"{file_path.stem}_{str(uuid.uuid4())[:8]}"
        return base_id.replace(" ", "_").replace("-", "_").lower()


def validate_medical_pdf(file_path: Path) -> Dict[str, any]:
    """
    Convenience function to validate a medical PDF.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Validation results
    """
    validator = MedicalPDFValidator()
    return validator.validate_file(file_path)