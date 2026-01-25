import pytest
from srp.server import run

@pytest.mark.asyncio
async def test_server_import():
    # Simple test to verify the module can be imported
    from srp import server
    assert server is not None
