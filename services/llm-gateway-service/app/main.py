"""Main FastAPI application for LLM Gateway Service."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import sys
import os

# Add shared directory to path
sys.path.append("/app/../../..")

# Set API keys from environment
from app.core.config import settings

# Set API keys for LLM providers
if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

if settings.ANTHROPIC_API_KEY:
    os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY

if settings.GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY

from app.api import llm_router

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    description="LLM Gateway Service for RaGenie - Unified interface to multiple LLM providers"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(llm_router)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "providers": {
            "openai": bool(settings.OPENAI_API_KEY),
            "anthropic": bool(settings.ANTHROPIC_API_KEY),
            "gemini": bool(settings.GEMINI_API_KEY)
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "providers_configured": sum([
            bool(settings.OPENAI_API_KEY),
            bool(settings.ANTHROPIC_API_KEY),
            bool(settings.GEMINI_API_KEY)
        ])
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print(f"{settings.APP_NAME} v{settings.VERSION} starting up...")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")

    # Check which providers are configured
    providers = []
    if settings.OPENAI_API_KEY:
        providers.append("OpenAI")
    if settings.ANTHROPIC_API_KEY:
        providers.append("Anthropic")
    if settings.GEMINI_API_KEY:
        providers.append("Google Gemini")

    if providers:
        print(f"Configured providers: {', '.join(providers)}")
    else:
        print("WARNING: No LLM provider API keys configured!")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print(f"{settings.APP_NAME} shutting down...")
