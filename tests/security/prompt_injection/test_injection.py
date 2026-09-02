from agents.database.sql_guard import SQLGuard

def test_sql_injection_guard():
    guard = SQLGuard()
    malicious = "SELECT * FROM users; DROP TABLE users; --"
    assert guard.validate_read_only(malicious) is False
    
    safe = "SELECT id, name FROM users WHERE organization_id = '123'"
    assert guard.validate_read_only(safe) is True
