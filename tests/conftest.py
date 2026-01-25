import pytest
from mcp.server import Server

@pytest.fixture
def server():
    return Server("srp-test")
