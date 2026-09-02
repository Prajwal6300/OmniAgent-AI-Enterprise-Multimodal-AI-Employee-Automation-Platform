from backend.app.core.security import decode_token, create_access_token
import pytest

def test_tampered_token_rejection():
    token = create_access_token("user-123")
    parts = token.split(".")
    tampered = f"{parts[0]}.{parts[1]}tampered.{parts[2]}"
    with pytest.raises(Exception):
        decode_token(tampered)
