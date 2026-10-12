import json
import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

from news_backend.config import setting, int_setting
from news_backend.images import resolve_article_image
from news_backend.prompts import NEWS_SYSTEM_PROMPT, NEWS_USER_PROMPT
from news_backend.storage import save_articles

logger = logging.getLogger(__name__)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def search_serp_news(topic: str, location: str, limit: int = 8) -> list[dict]:
    api_key = setting("SERP_API_KEY", required=True)
    params = {
        "engine": "google_news",
        "q": " ".join(x for x in [topic, location] if x),
        "api_key": api_key,
        "gl": setting("SERP_GL", "in"),
        "hl": setting("SERP_HL", "en"),
    }
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    results = payload.get("news_results") or payload.get("stories") or []
    articles = []
    for item in results[:max(1, min(limit, 30))]:
        link = item.get("link") or item.get("url")
        title = _clean_text(item.get("title", ""))
        if not link or not title:
            continue
        source = item.get("source") or {}
        if isinstance(source, dict):
            source_name = source.get("name")
        else:
            source_name = str(source) if source else None
        thumbnail = item.get("thumbnail") or item.get("thumbnail_small")
        if isinstance(thumbnail, dict):
            thumbnail = thumbnail.get("src") or thumbnail.get("url")
        articles.append({
            "serp_title": title,
            "url": link,
            "snippet": _clean_text(item.get("snippet", "")),
            "source": source_name,
            "published_at_raw": item.get("date"),
            "serp_image_url": thumbnail,
        })
    return articles


def scrape_article_text(url: str, max_chars: int = 16000) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NewsSummaryBot/1.0)",
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        response = requests.get(url, headers=headers, timeout=18)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for node in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            node.decompose()
        candidates = soup.select("article p, main p, [itemprop='articleBody'] p, p")
        paragraphs = [_clean_text(p.get_text(" ", strip=True)) for p in candidates]
        paragraphs = [p for p in paragraphs if len(p) > 45]
        text = "\n".join(dict.fromkeys(paragraphs))
        return text[:max_chars]
    except Exception as exc:
        logger.info("Could not scrape %s: %s", url, exc)
        return ""


def summarize_article(item: dict, topic: str, location: str) -> dict:
    api_key = setting("GEMINI_API_KEY", required=True)
    model = setting("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=api_key)
    article_text = scrape_article_text(item["url"])
    if len(article_text) < 250:
        article_text = item.get("snippet", "") or item["serp_title"]

    prompt = NEWS_USER_PROMPT.format(
        topic=topic,
        location=location,
        headline=item["serp_title"],
        snippet=item.get("snippet", ""),
        url=item["url"],
        article_text=article_text[:12000],
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=NEWS_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    raw = response.text or ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.S)
        if not match:
            raise RuntimeError(f"Gemini did not return JSON for: {item['serp_title']}")
        data = json.loads(match.group(0))

    title = _clean_text(data.get("title") or item["serp_title"])
    content = (data.get("content") or "").strip()
    if not content:
        content = item.get("snippet") or item["serp_title"]
    category = _clean_text(data.get("category") or topic) or topic
    return {
        "title": title,
        "content": content,
        "category": category,
        "location": location,
        "source": item.get("source"),
        "source_url": item["url"],
        "snippet": item.get("snippet"),
        "published_at_raw": item.get("published_at_raw"),
        "serp_image_url": item.get("serp_image_url"),
        "published_at": datetime.now(timezone.utc),
    }


def run_pipeline(topic: str, location: str, limit: int | None = None) -> dict:
    limit = limit or int_setting("NEWS_LIMIT", 8)
    raw_items = search_serp_news(topic, location, limit)
    articles = []
    image_enabled = setting("ENABLE_IMAGES", "true").lower() not in {"0", "false", "no"}

    for index, item in enumerate(raw_items, start=1):
        try:
            article = summarize_article(item, topic, location)
            if image_enabled:
                # Deterministic ID keeps re-runs from producing duplicate Cloudinary assets.
                slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", article["title"]).strip("-").lower()[:70]
                public_id = slug or f"news-{index}"
                image_url, image_source = resolve_article_image(
                    serp_image_url=item.get("serp_image_url"),
                    title=article["title"],
                    location=location,
                    topic=topic,
                    summary=article["content"],
                    public_id=public_id,
                )
                article["image_urls"] = [image_url] if image_url else []
                article["image_url"] = image_url
                article["image_source"] = image_source
            else:
                article["image_urls"] = []
                article["image_url"] = None
                article["image_source"] = "disabled"
            articles.append(article)
        except Exception as exc:
            logger.exception("Failed processing article %s: %s", item.get("serp_title"), exc)

    saved = save_articles(articles) if articles else 0
    return {
        "requested": len(raw_items),
        "processed": len(articles),
        "saved": saved,
        "topic": topic,
        "location": location,
        "articles": articles,
    }
