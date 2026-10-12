# 📰 AI-Powered News Aggregation & Summarization Platform

An AI-powered news platform that collects news from SERP API, extracts article text when available, generates concise summaries with Gemini, manages images through Cloudinary, and stores articles in MongoDB. A React frontend lets readers browse news by category and switch between the original article text and its AI-generated summary.

## ✨ Features

- **Automated news discovery:** Fetches news using SERP API based on configured topics and location.
- **Six topic categories:** Sports, Technology, Education, Crime, Political, and Others.
- **Article extraction:** Attempts to scrape article text from publisher pages; falls back to the SERP snippet when the publisher blocks scraping or text is unavailable.
- **AI summarization:** Uses the Gemini API to generate a separate title, summary, and category.
- **Original / Summary switch:** Readers can choose between extracted source text and the Gemini summary. Original is selected by default; when original text is unavailable, the frontend falls back to the summary.
- **Image handling:** Uploads available SERP thumbnails to Cloudinary. If an image is missing or cannot be uploaded, the backend attempts to generate an illustrative fallback image with Gemini and uploads it to Cloudinary.
- **Hourly background worker:** Processes the configured topics sequentially and repeats the cycle at the configured interval.
- **MongoDB persistence:** Stores articles and image URLs, with title-based upserts to reduce duplicate records.
- **Read-only public API:** The FastAPI service exposes endpoints to read stored news and check service health. News ingestion is performed by the separate worker, not a public `/fetch-news` route.

> **Image and source note:** Generated images are illustrative and should not be treated as documentary evidence. Only rehost third-party images when permitted by their licensing terms. Publisher scraping can be restricted, so original article text is not guaranteed for every result.

## 🧰 Tech Stack

- **Frontend:** React.js, Vite, Tailwind CSS (if configured in the frontend)
- **Backend API:** FastAPI, Uvicorn
- **Background processing:** Python worker (`server.py`)
- **Database:** MongoDB / MongoDB Atlas
- **News search:** SerpAPI Google News
- **Summarization and image fallback:** Google Gemini API
- **Article extraction:** Requests, BeautifulSoup
- **Image hosting:** Cloudinary

## 🏗 Architecture

```text
React frontend
     |
     | GET /news
     v
FastAPI public API (app.py) -----> MongoDB
                                      ^
                                      |
Private hourly worker (server.py) ---+
     |
     +--> SERP API: search news by topic and location
     +--> BeautifulSoup: extract publisher article text when accessible
     +--> Gemini: generate article summary
     +--> Cloudinary: upload SERP image or generated fallback
```

The API and worker run as separate processes. The worker does not expose an HTTP endpoint.

## 📁 Project Structure

```text
project/
├── app.py                       # FastAPI public read-only API
├── server.py                    # Private hourly news worker
├── news_backend/
│   ├── config.py                # Environment configuration
│   ├── news_pipeline.py         # Search, scrape, summarize, process and save news
│   ├── images.py                # Cloudinary upload and image fallback
│   ├── prompts.py               # Gemini prompts
│   └── storage.py               # MongoDB operations
├── .env                         # Local secrets; do not commit
├── .env.example                 # Environment variable template
├── requirements.txt             # Python dependencies
└── README.md
```

Your React frontend is maintained separately and contains `src/App.jsx` and the `Navbar` and `Footer` components.

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/hardiksirohiya/NewsProject.git
cd NewsProject
```

Adjust the directory names in the following steps if your backend and frontend are stored in separate folders.

### 2. Create and activate a Python environment

**Windows CMD:**

```cmd
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

Run this from the directory containing `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and enter your own credentials. Do not commit `.env` to GitHub.

```dotenv
SERP_API_KEY=your_serpapi_key
GEMINI_API_KEY=your_gemini_api_key

MONGODB_URI=your_mongodb_connection_string
MONGODB_DATABASE=news_app
MONGODB_COLLECTION=articles

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
CLOUDINARY_FOLDER=news-images

GEMINI_TEXT_MODEL=gemini-2.5-flash
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image

NEWS_TOPICS=Sports,Technology,Education,Crime,Political,Others
DEFAULT_LOCATION=India
NEWS_LIMIT_PER_TOPIC=8
WORKER_INTERVAL_SECONDS=3600
WORKER_RUN_ON_START=true
ENABLE_IMAGES=true

HOST=0.0.0.0
PORT=5000
CORS_ORIGINS=*
```

Use the exact variable names provided in your project's `.env.example`. Gemini image generation requires a model and API account that support image output. Keep all API secrets on the backend.

## ▶️ Run the Backend

The API and worker must run in separate terminals.

### Terminal 1: Start the FastAPI API

```bash
python -m uvicorn app:app --host 0.0.0.0 --port 5000
```

For local-only development, you can use `--host 127.0.0.1` instead.

### Terminal 2: Start the private hourly worker

```bash
python server.py
```

With `WORKER_RUN_ON_START=true`, the worker begins a topic cycle immediately and then waits for the configured interval before starting the next cycle. With `WORKER_INTERVAL_SECONDS=3600`, it waits one hour after each completed cycle.

The worker processes these topics sequentially:

1. Sports
2. Technology
3. Education
4. Crime
5. Political
6. Others

`NEWS_LIMIT_PER_TOPIC=8` requests up to eight results per topic; the actual number may be lower depending on SERP results and processing success.

For production, run both processes under a process manager or hosting platform that restarts them after failure. Deploy the worker as a private background process and do not expose a separate public port for it.

## 🌐 API Endpoints

### Health check

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

### Retrieve news

```http
GET /news
GET /news?limit=20
GET /news?topic=Technology&location=India&limit=20
```

Example response shape:

```json
{
  "count": 1,
  "news": [
    {
      "title": "Example news headline",
      "content": "AI-generated summary of the article...",
      "summary": "AI-generated summary of the article...",
      "original_content": "Extracted original article text, when available...",
      "category": "Technology",
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

The `image_source` value can indicate whether the image came from SERP, was generated as a fallback, was unavailable, or was disabled. Actual response fields depend on the data saved in MongoDB.

### Interactive API documentation

When the API is running, open:

- `http://localhost:5000/docs` — Swagger UI
- `http://localhost:5000/redoc` — ReDoc

There is intentionally no public `POST /fetch-news` endpoint. The private worker invokes the pipeline directly.

## 🖥️ Frontend Setup

From your React/Vite frontend directory:

```bash
npm install
npm run dev
```

Create or update the frontend `.env` file with the backend address:

```dotenv
VITE_BACKEND_URL=localhost:5000
```

The frontend should call:

```javascript
fetch(`http://${import.meta.env.VITE_BACKEND_URL}/news?limit=100`);
```

If `VITE_BACKEND_URL` already includes `http://` or `https://`, ensure your frontend URL-building logic does not add the protocol a second time.

The news cards support an **Original / Summary** switch. Original content is the default; summary displays the Gemini-generated version. The original text may be unavailable for some publishers, in which case the UI should show the available summary as a fallback.

## 🔐 Security and Operations

- Never commit `.env` or publish API secrets.
- Do not expose Cloudinary's API secret in the React frontend.
- Keep the worker private; only the FastAPI read endpoints should be publicly exposed unless authentication is added.
- The `/news` endpoint is public/read-only in the current setup. Add authentication or proxy restrictions if the news content should be private.
- Avoid running multiple worker instances unless concurrent ingestion is intended. Multiple workers may cause duplicate API usage and overlapping processing.
- Check logs for SERP, scraping, Gemini, Cloudinary, and MongoDB errors.

## ⚠️ Limitations

- Publisher sites may block scraping or return incomplete article text.
- SERP snippets are not equivalent to the complete original article.
- Gemini-generated summaries may omit nuance; review important news before republishing.
- Gemini image generation may not be available for every model or API account. If image processing fails, an article may be stored without an image.
- Title-based upserts reduce duplicates but do not guarantee that differently titled reports about the same event are merged.

## 📜 License

Add or update this section to match the license actually included in the repository.
