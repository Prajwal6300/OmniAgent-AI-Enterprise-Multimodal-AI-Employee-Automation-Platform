import base64
import json

import pytest
from fastapi import HTTPException

from app.core.security import create_access_token, decode_token


def test_tampered_token_rejection():
    token = create_access_token("user-123")
    parts = token.split(".")
    tampered = f"{parts[0]}.{parts[1]}tampered.{parts[2]}"
    with pytest.raises(HTTPException) as exc_info:
        decode_token(tampered)
    assert exc_info.value.status_code == 401


def test_wrong_secret_rejection():
    import jwt

    # Token signed with wrong secret -> 401
    wrong_secret_token = jwt.encode(
        {"exp": 9999999999, "sub": "user-123", "type": "access"},
        "wrong-secret-key",
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as exc_info:
        decode_token(wrong_secret_token)
    assert exc_info.value.status_code == 401


def test_alg_none_rejection():
    # Manually construct a JWT with alg=none header
    payload = {"exp": 9999999999, "sub": "user-123", "type": "access"}
    header = {"alg": "none", "typ": "JWT"}

    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    signature = base64.urlsafe_b64encode(b"").rstrip(b"=").decode()
    alg_none_token = f"{header_b64}.{payload_b64}.{signature}"
    # decode with explicit algorithm list should reject "none"
    with pytest.raises(HTTPException) as exc_info:
        decode_token(alg_none_token)
    assert exc_info.value.status_code == 401


def test_wrong_algorithm_rejection():
    import jwt

    from app.core.config import settings
    # Token with alg HS512 header -> 401 (our decode only allows HS256)
    hs512_token = jwt.encode(
        {"exp": 9999999999, "sub": "user-123", "type": "access"},
        settings.JWT_SECRET,
        algorithm="HS512",
    )
    with pytest.raises(HTTPException) as exc_info:
        decode_token(hs512_token)
    assert exc_info.value.status_code == 401


def test_expired_token_rejection():
    from datetime import UTC as utc_mod
    from datetime import datetime, timedelta

    import jwt


    # Create an explicitly expired token
    expired_payload = {
        "exp": datetime.now(utc_mod) - timedelta(hours=1),
        "sub": "user-123",
        "type": "access",
    }
    expired_token = jwt.encode(expired_payload, "some-secret", algorithm="HS256")
    with pytest.raises(HTTPException) as exc_info:
        decode_token(expired_token)
    assert exc_info.value.status_code == 401


def test_token_missing_sub_rejection():
    import jwt

    from app.core.config import settings
    payload = {"exp": 9999999999, "type": "access"}
    missing_sub_token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    with pytest.raises(HTTPException) as exc_info:
        decode_token(missing_sub_token)
    assert exc_info.value.status_code == 401


def test_valid_token_accepts():
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"