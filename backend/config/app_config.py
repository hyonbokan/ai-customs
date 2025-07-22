import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

class AppConfig:
    """Configuration for general application settings."""

    # Application metadata
    TITLE = "CustomsAI - APIs"
    DESCRIPTION = "API for detecting custom declaration discrepancies in international trade."
    VERSION = "0.1.0"

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    # Core API Keys
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

    # URLs
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", "localhost")

    # Host and port
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    @classmethod
    def get_full_version(cls) -> str:
        """Get full version string with title."""
        return f"{cls.TITLE} v{cls.VERSION}"
