from langchain_openai import AzureOpenAIEmbeddings
from backend.config import settings


def get_azure_embeddings() -> AzureOpenAIEmbeddings:
    """
    Instantiates and returns the AzureOpenAIEmbeddings client
    configured strictly using the dedicated embedding deployment setting.
    """
    settings.validate_azure_embedding_config()

    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    )
