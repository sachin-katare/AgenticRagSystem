from fastapi import FastAPI

from app.api.routers import analysis, ask, documents, search
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.utils.safe_logging import safe_log_fields


settings = get_settings()
logger = configure_logging(settings)

app = FastAPI(title=settings.app_name)
app.include_router(analysis.router)
app.include_router(ask.router)
app.include_router(documents.router)
app.include_router(search.router)


@app.get("/health-check")
def health_check() -> dict[str, str]:
    """Return a lightweight API/configuration health check."""
    logger.info("health_check %s", safe_log_fields({"route": "/health-check", "status": "ok"}))
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "llm_provider": settings.llm_provider,
        "chat_model": settings.ollama_chat_model,
        "embedding_model": settings.ollama_embedding_model,
    }
