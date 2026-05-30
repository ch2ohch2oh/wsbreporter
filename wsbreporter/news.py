import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from . import config


def build_news_context_from_queries(
    queries: list[str],
) -> tuple[str, list[dict[str, Any]]]:
    if not queries:
        return "", []

    context_lines = ["External News Context:"]
    used_items = []
    for query in queries[: config.NEWS_MAX_TERMS]:
        items = _load_or_fetch(query)
        if not items:
            continue

        context_lines.append(f"{query}:")
        for item in items[: config.NEWS_ITEMS_PER_TERM]:
            used_items.append(item)
            context_lines.append(f"- Title: {item.get('title', '')}")
            if item.get("source_name"):
                context_lines.append(f"  Source: {item['source_name']}")
            if item.get("published_at"):
                context_lines.append(f"  Published: {item['published_at']}")
            if item.get("summary"):
                context_lines.append(f"  Summary: {item['summary']}")
            context_lines.append(f"  URL: {item.get('url', '')}")

    if not used_items:
        return "", []

    return "\n".join(context_lines) + "\n", used_items


def _load_or_fetch(query: str) -> list[dict[str, Any]]:
    try:
        fetched = _fetch_google_news_rss(query)
    except Exception as e:
        print(f"News fetch failed for '{query}': {e}")
        return []
    if not fetched:
        return []
    return fetched[: config.NEWS_ITEMS_PER_TERM]


def _fetch_google_news_rss(query: str) -> list[dict[str, Any]]:
    encoded_query = urllib.parse.urlencode(
        {
            "q": query,
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en",
        }
    )
    url = f"https://news.google.com/rss/search?{encoded_query}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "wsbreporter/0.1 (+https://github.com/)"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        xml_bytes = response.read()

    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.findall("./channel/item"):
        title = _clean_text(item.findtext("title"))
        link = _clean_text(item.findtext("link"))
        if not title or not link:
            continue
        source = item.find("source")
        items.append(
            {
                "provider": config.NEWS_PROVIDER,
                "query": query,
                "title": title,
                "url": link,
                "source_name": _clean_text(source.text if source is not None else ""),
                "published_at": _parse_rss_datetime(item.findtext("pubDate")),
                "summary": _clean_text(item.findtext("description")),
                "raw": ET.tostring(item, encoding="unicode"),
            }
        )
        if len(items) >= config.NEWS_ITEMS_PER_TERM:
            break

    return items


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def _parse_rss_datetime(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError, IndexError, OverflowError):
        try:
            return datetime.fromisoformat(value).isoformat(timespec="seconds")
        except ValueError:
            return value
