import pytest
import os
import sys

# Ensure backend and modular packages are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "backend"))

@pytest.fixture
def sample_tenant_id():
    return "00000000-0000-0000-0000-000000000001"
