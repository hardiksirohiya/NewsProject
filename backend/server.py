"""Private background worker: process each configured topic sequentially every hour.

This process does not open an HTTP port or expose any endpoints.
"""
import logging
import signal
import threading

from news_backend.config import int_setting, setting
from news_backend.news_pipeline import run_pipeline

logging.basicConfig(
    level=setting("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("news_worker")
stop_event = threading.Event()
DEFAULT_TOPICS = ["Sports", "Technology", "Education", "Crime", "Political", "Others"]


def request_stop(signum, frame):
    logger.info("Received shutdown signal; stopping worker after current operation.")
    stop_event.set()


def configured_topics():
    raw = setting("NEWS_TOPICS", ",".join(DEFAULT_TOPICS))
    topics = [item.strip() for item in raw.split(",") if item.strip()]
    return topics or DEFAULT_TOPICS


def fetch_all_topics():
    location = setting("DEFAULT_LOCATION", "India")
    limit = int_setting("NEWS_LIMIT_PER_TOPIC", int_setting("NEWS_LIMIT", 8))
    topics = configured_topics()
    logger.info("Starting news cycle for %d topics: %s", len(topics), ", ".join(topics))
    totals = {"requested": 0, "processed": 0, "saved": 0}

    for topic in topics:
        if stop_event.is_set():
            logger.info("Stop requested; ending topic cycle early.")
            break
        logger.info("Fetching topic: %s", topic)
        try:
            result = run_pipeline(topic=topic, location=location, limit=limit)
            for key in totals:
                totals[key] += int(result.get(key, 0) or 0)
            logger.info(
                "Topic '%s' complete: requested=%s processed=%s saved=%s",
                topic, result.get("requested", 0), result.get("processed", 0), result.get("saved", 0),
            )
        except Exception:
            # One failed category should not prevent the remaining categories from running.
            logger.exception("Topic '%s' failed; continuing with the next topic.", topic)

    logger.info(
        "News cycle complete: requested=%s processed=%s saved=%s",
        totals["requested"], totals["processed"], totals["saved"],
    )


def main():
    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    interval = max(60, int_setting("WORKER_INTERVAL_SECONDS", 3600))
    run_on_start = setting("WORKER_RUN_ON_START", "true").lower() in {"1", "true", "yes"}
    logger.info("Private news worker started. Interval: %s seconds.", interval)
    if run_on_start:
        fetch_all_topics()

    while not stop_event.is_set():
        if stop_event.wait(interval):
            break
        fetch_all_topics()
    logger.info("News worker stopped.")


if __name__ == "__main__":
    main()
