from datetime import datetime
from time import sleep
from urllib.parse import urlparse

import requests
from flask import current_app


class NewsAPIService:
    """Small GNews client that normalizes responses for templates."""

    CATEGORIES = {"general", "world", "nation", "business", "technology", "entertainment", "sports", "science", "health"}

    # Statuses worth retrying (transient server errors / rate limits).
    RETRYABLE = {429, 500, 502, 503, 504}

    @staticmethod
    def _request(endpoint, params=None, attempts=3):
        api_key = current_app.config.get("GNEWS_API_KEY")
        if not api_key:
            return [], "GNews API key is missing. Add GNEWS_API_KEY to your .env file."

        request_params = {"token": api_key, "lang": "en", "max": 10, **(params or {})}
        last_message = "Sorry, we couldn't load the latest news. Please try again later."

        for attempt in range(1, attempts + 1):
            try:
                response = requests.get(
                    f"{current_app.config['GNEWS_BASE_URL']}/{endpoint}",
                    params=request_params,
                    timeout=12,
                )
                if response.status_code in NewsAPIService.RETRYABLE and attempt < attempts:
                    # Back off briefly before retrying (0.5s, 1s, ...).
                    sleep(0.5 * attempt)
                    continue
                response.raise_for_status()
                payload = response.json()
                return [NewsAPIService.normalize(article) for article in payload.get("articles", [])], None
            except requests.exceptions.HTTPError as error:
                status = error.response.status_code if error.response else 500
                # Log the real response body so the cause is visible in the server logs.
                body = ""
                if error.response is not None:
                    try:
                        body = error.response.text[:500]
                    except Exception:  # pragma: no cover - defensive
                        body = ""
                current_app.logger.warning("GNews HTTP error %s: %s", status, body)
                if status == 401:
                    last_message = "The news service API key is invalid."
                elif status == 403:
                    last_message = "The news service request limit has been reached."
                elif status == 429:
                    last_message = "Too many news requests. Please try again shortly."
                else:
                    last_message = "The news service is temporarily unavailable."
                if status in NewsAPIService.RETRYABLE and attempt < attempts:
                    sleep(0.5 * attempt)
                    continue
                return [], last_message
            except (requests.RequestException, ValueError) as error:
                current_app.logger.warning("GNews request failed (attempt %s): %s", attempt, error)
                last_message = "Sorry, we couldn't load the latest news. Please try again later."
                if attempt < attempts:
                    sleep(0.5 * attempt)
                    continue
                return [], last_message

        return [], last_message

    @staticmethod
    def normalize(article):
        source = article.get("source") or {}
        published = article.get("publishedAt") or ""
        try:
            display_date = datetime.fromisoformat(published.replace("Z", "+00:00")).strftime("%b %d, %Y")
        except ValueError:
            display_date = published
        return {
            "title": article.get("title") or "Untitled news story",
            "description": article.get("description") or "No description is available for this story.",
            "content": article.get("content") or article.get("description") or "The publisher has not supplied additional content.",
            "image": article.get("image") or "",
            "url": article.get("url") or "#",
            "source": source.get("name") or "Unknown source",
            "source_url": source.get("url") or "",
            "published_at": published,
            "display_date": display_date,
            "author": article.get("author") or source.get("name") or "Editorial desk",
        }

    @classmethod
    def top_headlines(cls, category="general", page=1, limit=10):
        category = category if category in cls.CATEGORIES else "general"
        return cls._request("top-headlines", {"category": category, "max": limit, "page": page})

    @classmethod
    def search(cls, query, page=1, limit=10):
        return cls._request("search", {"q": query, "max": limit, "page": page, "sortby": "publishedAt"})

    @classmethod
    def article_from_request(cls, values):
        article_url = values.get("url", "")
        if not article_url or urlparse(article_url).scheme not in {"http", "https"}:
            return None
        return {
            "title": values.get("title", "Untitled news story"),
            "description": values.get("description", "No description is available."),
            "content": values.get("content", values.get("description", "")),
            "image": values.get("image", ""),
            "url": article_url,
            "source": values.get("source", "Unknown source"),
            "published_at": values.get("published_at", ""),
            "display_date": values.get("display_date", values.get("published_at", "")),
            "author": values.get("author", "Editorial desk"),
        }
