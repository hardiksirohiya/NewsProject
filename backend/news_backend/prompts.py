"""Prompts used by the news summarization and image fallback workflow."""

NEWS_SYSTEM_PROMPT = """
You are a careful news editor. Write clear, neutral, factual news summaries.
Use only facts supported by the supplied source material. Do not invent quotes,
numbers, causes, dates, names, or details. If sources disagree, describe only
what is well-supported and note uncertainty when important.
Return valid JSON with these keys:
title: concise headline
content: an article-style summary with an Introduction paragraph followed by
useful paragraphs. Do not include markdown fences or a separate title heading
inside content. Preserve relevant dates, locations, names, and context.
category: short topic category
"""

NEWS_USER_PROMPT = """
Create a useful news article summary from the source material below.
Requested topic: {topic}
Requested location: {location}
Search headline: {headline}
Search snippet: {snippet}
Source URL: {url}
Extracted article text:
{article_text}

Return only a JSON object with keys title, content, category.
The content must start with an Introduction paragraph and should be concise,
balanced, readable, and grounded in the provided text.
"""

IMAGE_FALLBACK_PROMPT = """
Create a professional editorial illustration for a news website based on the
following story. Depict the general subject in a realistic, visually clear way.
Use documentary-style composition, natural lighting, and believable details.
This is an illustrative image, not a claim that a specific photographed event
occurred. Do not include text, letters, captions, logos, watermarks, charts, or
graphic overlays. Avoid sensationalism and avoid depicting identifiable private
individuals.

Headline: {title}
Location: {location}
Topic: {topic}
Story summary: {summary}
"""
