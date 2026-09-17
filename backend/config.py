import os
import sys
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


def ensure_windows_dlls():
    """Ensures MSVC runtime DLLs (like MSVCP140.dll) can be located on Windows."""
    if sys.platform == "win32":
        candidates = [
            r"C:\Windows\System32\Microsoft-Edge-WebView",
            r"C:\Program Files\Microsoft RDInfra\RDAgentBootLoader_1.0.13074.100\x64",
        ]
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            onedrive_dir = Path(localappdata) / "Microsoft" / "OneDrive"
            if onedrive_dir.exists():
                for sub in onedrive_dir.iterdir():
                    if sub.is_dir() and (sub / "msvcp140.dll").exists():
                        candidates.append(str(sub))

        venv_scripts = Path(sys.executable).parent
        if venv_scripts.exists():
            candidates.append(str(venv_scripts))

        for path in candidates:
            if os.path.exists(path):
                try:
                    os.add_dll_directory(path)
                except Exception:
                    pass


ensure_windows_dlls()


def ensure_private_endpoint_resolution():
    """
    Pins local DNS resolution for known Azure Private Endpoints,
    preventing intermittent DNS leaks to public servers that trigger 403 Forbidden.
    """
    import socket

    _orig_getaddrinfo = socket.getaddrinfo

    def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if host == "capstone-openai-mfg.openai.azure.com":
            return _orig_getaddrinfo("192.168.1.30", port, family, type, proto, flags)
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = patched_getaddrinfo


ensure_private_endpoint_resolution()


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or invalid."""
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure OpenAI Chat Configuration
    AZURE_OPENAI_API_KEY: str = Field(default="", description="Azure OpenAI API Key")
    AZURE_OPENAI_ENDPOINT: str = Field(default="", description="Azure OpenAI Endpoint URL")
    AZURE_OPENAI_API_VERSION: str = Field(default="2024-02-01", description="Azure OpenAI API Version")
    AZURE_OPENAI_DEPLOYMENT: str = Field(default="gpt-5.1", description="Azure OpenAI Chat Deployment Name")

    # Azure OpenAI Embeddings Configuration
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = Field(
        default="", description="Azure OpenAI Embedding Deployment Name"
    )

    # Retrieval Configuration
    TOP_K: int = Field(default=5, description="Number of policy chunks to retrieve")

    # Paths
    BASE_DIR: Path = BASE_DIR
    KNOWLEDGE_BASE_DIR: Path = BASE_DIR / "knowledge_base"
    CHROMA_PERSIST_DIR: Path = BASE_DIR / "chroma_db"
    CHROMA_COLLECTION_NAME: str = "company_policies"

    # Backend / Frontend Communication
    BACKEND_URL: str = Field(default="http://localhost:8000", description="Backend service URL")
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    def validate_azure_chat_config(self) -> None:
        """Validates that chat model configuration parameters are present."""
        missing = []
        if not self.AZURE_OPENAI_API_KEY or self.AZURE_OPENAI_API_KEY == "your-api-key":
            missing.append("AZURE_OPENAI_API_KEY")
        if not self.AZURE_OPENAI_ENDPOINT or "your-resource" in self.AZURE_OPENAI_ENDPOINT:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not self.AZURE_OPENAI_DEPLOYMENT:
            missing.append("AZURE_OPENAI_DEPLOYMENT")
        if not self.AZURE_OPENAI_API_VERSION:
            missing.append("AZURE_OPENAI_API_VERSION")

        if missing:
            raise ConfigurationError(
                f"Missing or placeholder Azure OpenAI Chat configuration: {', '.join(missing)}. "
                "Please update your .env file with valid Azure OpenAI credentials."
            )

    def validate_azure_embedding_config(self) -> None:
        """Validates that embedding model configuration parameters are present."""
        missing = []
        if not self.AZURE_OPENAI_API_KEY or self.AZURE_OPENAI_API_KEY == "your-api-key":
            missing.append("AZURE_OPENAI_API_KEY")
        if not self.AZURE_OPENAI_ENDPOINT or "your-resource" in self.AZURE_OPENAI_ENDPOINT:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if (
            not self.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            or self.AZURE_OPENAI_EMBEDDING_DEPLOYMENT == "your-embedding-deployment"
        ):
            missing.append("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        if missing:
            raise ConfigurationError(
                f"Missing or placeholder Azure OpenAI Embedding configuration: {', '.join(missing)}. "
                "Please update your .env file with valid Azure OpenAI embedding credentials."
            )

    def is_azure_configured(self) -> bool:
        """Helper to check if all Azure configurations are filled without throwing."""
        try:
            self.validate_azure_chat_config()
            self.validate_azure_embedding_config()
            return True
        except ConfigurationError:
            return False


settings = Settings()
