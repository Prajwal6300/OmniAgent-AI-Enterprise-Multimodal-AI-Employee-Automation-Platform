import pytest
from backend.app.core.security import create_access_token, decode_token
from jose import JWTError


def test_tampered_token_rejection():
    token = create_access_token("user-123")
    parts = token.split(".")
    tampered = f"{parts[0]}.{parts[1]}tampered.{parts[2]}"
    with pytest.raises(JWTError):
        decode_token(tampered)
