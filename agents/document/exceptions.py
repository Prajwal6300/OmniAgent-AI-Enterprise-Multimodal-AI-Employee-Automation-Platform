try:
    from app.core.exceptions import BaseAppException
except ImportError:
    try:
        from backend.app.core.exceptions import BaseAppException
    except ImportError:
        class BaseAppException(Exception):
            def __init__(self, message: str, details: dict | None = None):
                self.message = message
                self.details = details or {}
                super().__init__(self.message)


class DocumentAgentException(BaseAppException):
    """Base exception for Document Agent operations."""


class DocumentValidationError(DocumentAgentException):
    """Raised when file validation, format, size, or path checks fail."""


class DocumentExtractionError(DocumentAgentException):
    """Raised when parsing or extracting text from a document fails."""


class DocumentProcessingError(DocumentAgentException):
    """Raised when an internal error occurs during document analysis pipeline."""


class DocumentNotFoundError(DocumentAgentException):
    """Raised when target document does not exist or storage path is missing."""


class DocumentAuthorizationError(DocumentAgentException):
    """Raised when user/tenant lacks authorization to access or analyze target document."""


class DocumentLLMError(DocumentAgentException):
    """Raised when LLM inference, structured output decoding, or timeout occurs."""
