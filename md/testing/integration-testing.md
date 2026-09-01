# Testing — Integration Testing & Database Mocking

## Status
**Status:** ✅ IMPLEMENTED (Testcontainers & Asyncpg SQLite/PostgreSQL)

---

## 1. Database Integration Testing

Integration tests run against a live PostgreSQL 16 container with `pgvector` enabled using `testcontainers-python` to ensure authentic SQL dialect execution.

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_and_query_document(async_client: AsyncClient, test_jwt_token: str):
    headers = {"Authorization": f"Bearer {test_jwt_token}"}
    response = await async_client.post(
        "/api/v1/documents/presigned",
        json={"filename": "test_sop.pdf", "mime_type": "application/pdf", "file_size_bytes": 1024},
        headers=headers
    )
    assert response.status_code == 200
    assert "upload_url" in response.json()["data"]
```
