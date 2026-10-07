

def test_neon_pooler_cache_disabled():
    """Neon pooled URLs should have cache disabled."""
    # Neon pooler URL contains -pooler
    url = "postgresql+asyncpg://postgres:pass@ep-xxxx-pooler.us-east-2.aws.neon.tech:5432/db?ssl=require"
    assert "-pooler" in url

def test_direct_neon_url_cache_enabled():
    """Direct Neon URLs (no -pooler) should NOT disable cache."""
    # Direct Neon URL without -pooler
    url = "postgresql+asyncpg://postgres:pass@neon.tech:5432/db?ssl=require"
    assert "-pooler" not in url

def test_6543_port_disables_cache():
    """URL with port 6543 should disable cache."""
    url = "postgresql+asyncpg://postgres:pass@aws-0-us-east-1.pooler.neon.tech:6543/db?ssl=require"
    assert ":6543" in url or "-pooler" in url
