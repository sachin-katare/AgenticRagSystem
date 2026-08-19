from fastapi import FastAPI

from app.api.routers import analysis, ask, documents, search
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(title=settings.app_name)
app.include_router(analysis.router)
app.include_router(ask.router)
app.include_router(documents.router)
app.include_router(search.router)


@app.get("/health-check")
def health_check() -> dict[str, str]:
    """Return a lightweight API/configuration health check."""
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "llm_provider": settings.llm_provider,
        "chat_model": settings.ollama_chat_model,
        "embedding_model": settings.ollama_embedding_model,
    }
