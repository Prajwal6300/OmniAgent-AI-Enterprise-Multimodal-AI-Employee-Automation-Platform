from fastapi import HTTPException, status

class BaseAppException(Exception):
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(BaseAppException):
    pass

class AuthenticationError(BaseAppException):
    pass

class AuthorizationError(BaseAppException):
    pass

class AgentError(BaseAppException):
    pass

class ToolExecutionError(BaseAppException):
    pass

class RAGError(BaseAppException):
    pass

class MultimodalProcessingError(BaseAppException):
    pass

class WorkflowError(BaseAppException):
    pass

class ExternalServiceError(BaseAppException):
    pass
