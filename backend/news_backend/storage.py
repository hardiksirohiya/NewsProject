from datetime import datetime, timezone
from pymongo import MongoClient, DESCENDING
from pymongo.errors import PyMongoError
from news_backend.config import setting


_client = None


def get_collection():
    global _client
    mongo_uri = setting("MONGODB_URI", required=True)
    db_name = setting("MONGODB_DATABASE", "news_app")
    collection_name = setting("MONGODB_COLLECTION", "articles")
    if _client is None:
        _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=8000)
    return _client[db_name][collection_name]


def save_articles(articles: list[dict]) -> int:
    """Upsert by normalized title so reruns update rather than duplicate stories."""
    collection = get_collection()
    saved = 0
    for article in articles:
        title = (article.get("title") or "").strip()
        if not title:
            continue
        doc = dict(article)
        doc["title"] = title
        doc.pop("created_at", None)
        doc["updated_at"] = datetime.now(timezone.utc)
        collection.update_one(
            {"title_key": title.casefold()},
            {"$set": {**doc, "title_key": title.casefold()},
             "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
        saved += 1
    return saved


def list_articles(limit: int = 50, topic: str | None = None, location: str | None = None):
    collection = get_collection()
    query = {}
    if topic:
        query["category"] = {"$regex": topic, "$options": "i"}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    cursor = collection.find(query, {"_id": 0, "title_key": 0}).sort(
        [("published_at", DESCENDING), ("updated_at", DESCENDING)]
    ).limit(max(1, min(limit, 200)))
    results = []
    for doc in cursor:
        for key, value in list(doc.items()):
            if hasattr(value, "isoformat"):
                doc[key] = value.isoformat()
        results.append(doc)
    return results
