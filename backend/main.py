import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings, ConfigurationError
from backend.models import ChatRequest, ChatResponse, HealthResponse, RootResponse
from backend.rag.vector_store import VectorStoreNotFoundError, is_vector_store_populated
from backend.services.chat_service import ChatService, ChatServiceError

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("backend.main")

app = FastAPI(
    title="Company Policy RAG API",
    description="Production-grade API for company policy Q&A grounded in PDF knowledge base documents using Azure OpenAI and ChromaDB.",
    version="1.0.0",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ConfigurationError)
async def configuration_exception_handler(request: Request, exc: ConfigurationError):
    logger.warning(f"Configuration error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc)},
    )


@app.exception_handler(VectorStoreNotFoundError)
async def vector_store_exception_handler(request: Request, exc: VectorStoreNotFoundError):
    logger.warning(f"Vector store error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc)},
    )


@app.exception_handler(ChatServiceError)
async def chat_service_exception_handler(request: Request, exc: ChatServiceError):
    logger.error(f"Chat service error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log internal error without exposing stack trace or secrets to the user
    logger.error(f"Unhandled exception during request {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please verify backend logs."},
    )


@app.get(
    "/",
    response_model=RootResponse,
    summary="API Root Status",
    tags=["Status"],
)
async def root():
    """Returns basic service availability."""
    return RootResponse(
        status="ok",
        message="Company Policy RAG API is running",
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health & Readiness Check",
    tags=["Status"],
)
async def health():
    """
    Checks the readiness of the Azure configuration and ChromaDB vector store.
    """
    azure_ok = settings.is_azure_configured()
    vector_ok = is_vector_store_populated()
    kb_files = len(list(settings.KNOWLEDGE_BASE_DIR.glob("*.pdf"))) if settings.KNOWLEDGE_BASE_DIR.exists() else 0

    return HealthResponse(
        status="healthy",
        azure_configured=azure_ok,
        vector_store_ready=vector_ok,
        knowledge_base_files=kb_files,
    )


@app.post(
    "/api/chat",
    response_model=ChatResponse,
    summary="Query Company Policies",
    tags=["RAG Chat"],
    responses={
        200: {"description": "Grounded answer with policy citations"},
        400: {"description": "Invalid or empty question"},
        502: {"description": "Azure OpenAI communication failure"},
        503: {"description": "Missing configuration or unindexed vector store"},
    },
)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Receives an employee question, retrieves relevant chunks from the company policy vector database,
    and returns a grounded answer generated via Azure OpenAI with citations.
    """
    service = ChatService()
    return service.answer_question(request)
