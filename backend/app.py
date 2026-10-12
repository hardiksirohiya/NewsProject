"""FastAPI public, read-only news API gateway."""
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from news_backend.config import int_setting, setting
from news_backend.storage import list_articles

logging.basicConfig(
    level=setting("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("news_api")
app = FastAPI(
    title="News API",
    description="Read-only API for news stored in MongoDB. Ingestion runs in a private worker.",
    version="1.0.0",
)
origins = [x.strip() for x in setting("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=False if origins == ["*"] else True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/", tags=["system"])
def index():
    # Do not advertise internal worker details or any ingestion route.
    return {
        "name": "News API",
        "endpoints": {
            "health": "GET /health",
            "news": "GET /news?limit=20&topic=Technology&location=India",
            "documentation": "GET /docs",
        },
    }


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


@app.get("/news", tags=["news"])
def news(
    limit: int = Query(default=50, ge=1, le=200),
    topic: str | None = Query(default=None, max_length=100),
    location: str | None = Query(default=None, max_length=100),
):
    try:
        articles = list_articles(limit=limit, topic=topic, location=location)
        return {"count": len(articles), "news": articles}
    except Exception as exc:
        logger.exception("Unable to retrieve news")
        # Keep DB credentials and internal errors out of public responses.
        raise HTTPException(status_code=500, detail="Could not retrieve news") from exc
