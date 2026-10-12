import io
import logging
import requests
import cloudinary
import cloudinary.uploader
from google import genai
from google.genai import types

from news_backend.config import setting
from news_backend.prompts import IMAGE_FALLBACK_PROMPT

logger = logging.getLogger(__name__)


def configure_cloudinary():
    cloud_name = setting("CLOUDINARY_CLOUD_NAME", required=True)
    api_key = setting("CLOUDINARY_API_KEY", required=True)
    api_secret = setting("CLOUDINARY_API_SECRET", required=True)
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )


def upload_remote_image(image_url: str, public_id: str):
    """Upload a remote SERP thumbnail directly through Cloudinary's server API."""
    configure_cloudinary()
    response = cloudinary.uploader.upload(
        image_url,
        folder=setting("CLOUDINARY_FOLDER", "news-images"),
        public_id=public_id,
        overwrite=True,
        resource_type="image",
        timeout=30,
    )
    return response.get("secure_url")


def generate_image_bytes(title: str, location: str, topic: str, summary: str):
    api_key = setting("GEMINI_API_KEY", required=True)
    model = setting("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    client = genai.Client(api_key=api_key)
    prompt = IMAGE_FALLBACK_PROMPT.format(
        title=title, location=location, topic=topic, summary=summary[:1800]
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )
    for part in response.parts or []:
        inline_data = getattr(part, "inline_data", None)
        if inline_data and getattr(inline_data, "data", None):
            data = inline_data.data
            if isinstance(data, str):
                import base64
                data = base64.b64decode(data)
            return data
    raise RuntimeError(
        "Gemini returned no image bytes. Verify that the configured model supports "
        "image generation for your API account."
    )


def upload_generated_image(image_bytes: bytes, public_id: str):
    configure_cloudinary()
    response = cloudinary.uploader.upload(
        io.BytesIO(image_bytes),
        folder=setting("CLOUDINARY_FOLDER", "news-images"),
        public_id=public_id,
        overwrite=True,
        resource_type="image",
        timeout=60,
    )
    return response.get("secure_url")


def resolve_article_image(serp_image_url: str | None, title: str, location: str,
                          topic: str, summary: str, public_id: str):
    """
    Prefer SERP image -> upload to Cloudinary. If absent/unusable, generate fallback
    image and upload that. Returns (url, source_type).
    """
    if serp_image_url:
        try:
            # Check the URL is reachable before asking Cloudinary to ingest it.
            check = requests.get(
                serp_image_url,
                timeout=12,
                stream=True,
                headers={"User-Agent": "Mozilla/5.0 news-image-fetcher"},
            )
            content_type = check.headers.get("Content-Type", "").lower()
            check.close()
            if check.ok and (content_type.startswith("image/") or not content_type):
                url = upload_remote_image(serp_image_url, public_id)
                if url:
                    return url, "serp"
        except Exception as exc:
            logger.warning("SERP image upload failed for %s: %s", title, exc)

    try:
        image_bytes = generate_image_bytes(title, location, topic, summary)
        url = upload_generated_image(image_bytes, public_id)
        if url:
            return url, "generated"
    except Exception as exc:
        logger.exception("Fallback image generation/upload failed for %s: %s", title, exc)

    return None, "none"
