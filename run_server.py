import sys
import os
import asyncio

# Add src directory to the python path so 'srp' can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from srp.server import run

if __name__ == "__main__":
    asyncio.run(run())
