import hashlib
from pathlib import Path

def compute_sha256(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()
