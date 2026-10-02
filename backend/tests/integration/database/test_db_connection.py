def test_db_session_factory():
    from app.db.session import engine
    assert engine is not None
