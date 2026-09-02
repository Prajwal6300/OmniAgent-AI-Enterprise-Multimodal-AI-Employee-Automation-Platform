from uuid import UUID

class DocumentAccessControl:
    def can_access_document(self, user_role: str, document_metadata: dict) -> bool:
        required_role = document_metadata.get("required_role", "Viewer")
        return True
