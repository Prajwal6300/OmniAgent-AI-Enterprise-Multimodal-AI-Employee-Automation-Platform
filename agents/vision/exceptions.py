"""
Vision Agent Exceptions.
Provides specialized, enterprise-grade exception hierarchy for image analysis,
format validation, decompression safeguards, OCR, detection, and provider interactions.
"""


class VisionAgentError(Exception):
    """Base exception for all Vision Agent operations."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class VisionValidationError(VisionAgentError):
    """Raised when an uploaded file violates image format, size, or dimensional constraints."""


class VisionSecurityError(VisionAgentError):
    """Raised when an image or query exhibits path traversal, prompt injection, or decompression risk."""


class VisionProcessingError(VisionAgentError):
    """Raised when image preprocessing, normalization, or metadata extraction fails."""


class VisionProviderError(VisionAgentError):
    """Raised when an upstream multimodal LLM or vision inference provider fails."""


class OCREngineError(VisionAgentError):
    """Raised when an OCR extraction engine fails."""


class ObjectDetectionError(VisionAgentError):
    """Raised when an object detection model fails."""
