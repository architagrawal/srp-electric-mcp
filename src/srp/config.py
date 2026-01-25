import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv, set_key

# Load existing .env if present
load_dotenv()

ENV_PATH = Path(".env")

class Config:
    @staticmethod
    def get_username() -> Optional[str]:
        return os.getenv("SRP_USERNAME")

    @staticmethod
    def get_password() -> Optional[str]:
        return os.getenv("SRP_PASSWORD")

    @staticmethod
    def get_account_id() -> Optional[str]:
        return os.getenv("SRP_ACCOUNT_ID")

    @staticmethod
    def get_auth_host() -> str:
        return os.getenv("AUTH_HOST", "localhost")

    @staticmethod
    def get_auth_port() -> int:
        return int(os.getenv("AUTH_PORT", "8080"))

    @staticmethod
    def get_auth_realm() -> str:
        return os.getenv("AUTH_REALM", "master")

    @staticmethod
    def get_oauth_client_id() -> str:
        return os.getenv("OAUTH_CLIENT_ID", "srp-server")

    @staticmethod
    def get_oauth_client_secret() -> str:
        return os.getenv("OAUTH_CLIENT_SECRET", "")
    
    @staticmethod
    def get_mcp_scope() -> str:
        return os.getenv("MCP_SCOPE", "mcp:tools")

    @staticmethod
    def get_host() -> str:
        return os.getenv("HOST", "localhost")

    @staticmethod
    def get_port() -> int:
        return int(os.getenv("PORT", "3000"))

    @property
    def auth_base_url(self) -> str:
        """Build the auth server base URL."""
        return f"http://{Config.get_auth_host()}:{Config.get_auth_port()}/realms/{Config.get_auth_realm()}/"

    @staticmethod
    def save_credentials(username: str, password: str, account_id: str):
        """
        Saves credentials to the .env file.
        """
        if not ENV_PATH.exists():
            ENV_PATH.touch()

        # Update or add keys
        set_key(ENV_PATH, "SRP_USERNAME", username)
        set_key(ENV_PATH, "SRP_PASSWORD", password)
        set_key(ENV_PATH, "SRP_ACCOUNT_ID", account_id)
        
        # Reload to ensure current process sees changes
        load_dotenv(override=True)
