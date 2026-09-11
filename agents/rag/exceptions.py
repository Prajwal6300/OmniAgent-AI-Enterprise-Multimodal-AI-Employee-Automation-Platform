class RAGException(Exception):
    """Base exception class for all RAG Agent errors."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class RAGQueryError(RAGException):
    """Raised when an incoming query fails validation or parsing."""
    pass


class EmbeddingError(RAGException):
    """Raised when query or document vector embedding generation fails."""
    pass


class RetrievalError(RAGException):
    """Raised when vector database search fails or experiences connection errors."""
    pass


class ContextBuildError(RAGException):
    """Raised when context synthesis or injection defense processing fails."""
    pass


class RAGGenerationError(RAGException):
    """Raised when the LLM generation step fails or returns unparseable content."""
    pass


class GroundingValidationError(RAGException):
    """Raised when answer verification against supporting context fails."""
    pass


class DocumentNotIndexedError(RAGException):
    """Raised when a query targets a document that has not completed vector indexing."""
    pass


class UnauthorizedDocumentAccessError(RAGException):
    """Raised when a cross-tenant or unauthorized document retrieval is attempted."""
    pass
