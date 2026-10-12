# News Backend: Public News API + Private Hourly Worker

This project separates the public read-only API from the private news-ingestion worker.

## Architecture

- **`app.py`** — long-running FastAPI API. Public routes are `GET /news` and `GET /health`. It does not expose a `POST /fetch-news` route.
- **`server.py`** — private background worker. It processes Sports, Technology, Education, Crime, Political, and Others sequentially on startup (configurable), then repeats the full topic cycle every hour by default. It does not open an HTTP port or expose any endpoint.
- **SERP API** — searches for news matching the configured topic and location.
- **Gemini** — summarizes the article and creates a fallback image if no usable SERP thumbnail can be uploaded.
- **Cloudinary** — stores SERP images or generated fallback images.
- **MongoDB** — stores article title, content, category, source, and Cloudinary image URL.

## Setup

Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then fill in your own credentials:

- `SERP_API_KEY`
- `GEMINI_API_KEY`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`
- `MONGODB_URI`

Do not commit `.env`, and never put Cloudinary's API secret in React/frontend code.

## Configure the hourly worker

```dotenv
NEWS_TOPICS=Sports,Technology,Education,Crime,Political,Others
DEFAULT_LOCATION=India
NEWS_LIMIT_PER_TOPIC=8
WORKER_INTERVAL_SECONDS=3600
WORKER_RUN_ON_START=true
```

`NEWS_TOPICS` defines the sequential topic order. The worker finishes one topic before starting the next; an error in one topic does not stop the others. `NEWS_LIMIT_PER_TOPIC` sets the number of articles requested per topic. `WORKER_INTERVAL_SECONDS=3600` means one complete topic cycle per hour. With `WORKER_RUN_ON_START=true`, it runs a cycle at startup.

## Run both processes

Open two terminals in the project directory.

Terminal 1 — public API:

```bash
uvicorn app:app --host 0.0.0.0 --port 5000
```

Terminal 2 — private worker:

```bash
python server.py
```

The public API listens on `http://localhost:5000` by default. Keep the worker running as a separate process. In production, use a process manager such as systemd, Supervisor, Docker restart policies, or your hosting platform's worker service so both processes restart if they fail.

## Public endpoints

```http
GET /health
GET /news?limit=20
GET /news?topic=technology&location=India&limit=20
```

Example response:

```json
{
  "count": 1,
  "news": [
    {
      "title": "A separate headline",
      "content": "Introduction paragraph... Additional context...",
      "category": "technology",
      "location": "India",
      "source": "Publisher",
      "source_url": "https://publisher.example/article",
      "image_url": "https://res.cloudinary.com/...",
      "image_urls": ["https://res.cloudinary.com/..."],
      "image_source": "serp"
    }
  ]
}
```

## Keeping ingestion private

There is no public `/fetch-news` route. The worker invokes the Python pipeline directly, so a visitor cannot trigger API spending by calling an ingestion endpoint. The root `/` response advertises only public routes.

If you deploy behind a reverse proxy, expose only the FastAPI API service. Do not publish a separate port for the worker. Keep environment secrets server-side. The `/news` route is intentionally public/read-only; if the content itself should be private, add authentication to that route or restrict it at the reverse proxy.

## Image behavior

1. Use the SERP thumbnail if available and upload it to Cloudinary.
2. If the thumbnail is missing or fails, ask Gemini for an illustrative fallback image and upload that.
3. If both paths fail, save the story with no image URL.

Generated images are illustrative, not documentary evidence. Only rehost third-party SERP images when permitted by their licensing terms.

## Notes

- Websites can block scraping; when that happens the pipeline falls back to SERP snippets or headlines.
- MongoDB upserts use a normalized title key to reduce duplicate records.
- The article `title` is separate from `content`; the Introduction paragraph is retained.
- Do not run multiple worker instances unless you intentionally want concurrent fetches. For multiple replicas, add a distributed lock or use a dedicated scheduler.
