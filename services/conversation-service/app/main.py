"""Conversation Service main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.conversations import router as conversations_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events."""
    # Startup
    print(f"Starting {settings.APP_NAME}")
    print(f"Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    print(f"Document Service: {settings.DOCUMENT_SERVICE_URL}")
    print(f"LLM Gateway: {settings.LLM_GATEWAY_URL}")
    yield
    # Shutdown
    print(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversations_router, prefix="/conversations", tags=["conversations"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "endpoints": {
            "conversations": "/conversations",
            "messages": "/conversations/{id}/messages",
            "rag_context": "/conversations/{id}/context"
        }
    }
