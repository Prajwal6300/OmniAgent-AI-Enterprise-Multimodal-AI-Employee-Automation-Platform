from backend.app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing():
    raw = "SecureEnterprisePass123!"
    hashed = get_password_hash(raw)
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_generation():
    token = create_access_token(subject="user-uuid-123")
    assert isinstance(token, str)
    assert len(token.split(".")) == 3
