def test_db_session_factory():
    from backend.app.db.session import engine
    assert engine is not None
