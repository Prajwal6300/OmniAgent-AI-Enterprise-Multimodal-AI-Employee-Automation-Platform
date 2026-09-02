class FileUploadTrigger:
    def trigger(self, file_id: str, file_path: str) -> dict:
        return {"trigger_type": "FILE_UPLOAD", "file_id": file_id, "path": file_path}
