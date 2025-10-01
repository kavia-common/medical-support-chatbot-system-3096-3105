import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.chat import router as chat_router
from .config import settings

# PUBLIC_INTERFACE
def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application for the medical chatbot backend.

    Returns:
        FastAPI: Configured FastAPI instance with routers and middleware.
    """
    app = FastAPI(
        title="CrewAI Medical Support - Backend",
        description=(
            "FastAPI backend for a CrewAI-style multi-agent medical support chatbot demo.\n\n"
            "Important disclaimer: Recommendations are not medical advice. "
            "This system is for informational and demonstration purposes only."
        ),
        version="1.0.0",
        openapi_tags=[
            {"name": "Chat", "description": "Endpoints to interact with chat and retrieve chat history."},
            {"name": "Recommendations", "description": "Endpoints to fetch medical recommendations."},
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router, prefix="/api", tags=["Chat"])

    @app.get("/", summary="Service health", description="Basic health check endpoint.", tags=["Chat"])
    # PUBLIC_INTERFACE
    def health():
        """Health check endpoint"""
        return {"status": "ok", "service": "medical_chatbot_backend"}

    return app


app = create_app()
