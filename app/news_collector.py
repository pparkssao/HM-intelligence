"""News collection from RSS feeds."""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import re

import feedparser
import requests
from dateutil import parser as dateparser

from config import RSS_FEEDS, REQUEST_TIMEOUT, MAX_NEWS_PER_FEED

logger = logging.getLogger(__name__)


def _parse_date(entry: Dict[str, Any]) -> datetime | None:
    """Try multiple date fields and return a timezone-aware datetime."""
    for field in ("published", "updated", "created"):
        raw = entry.get(f"{field}_parsed") or entry.get(field)
        if raw:
            try:
                if hasattr(raw, "tm_year"):  # time.struct_time from feedparser
                    import calendar
                    ts = calendar.timegm(raw)
                    return datetime.fromtimestamp(ts, tz=timezone.utc)
                return dateparser.parse(str(raw)).astimezone(timezone.utc)
            except Exception:
                continue
    return None


def _clean_html(text: str) -> str:
    """Strip HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", text or "").strip()


def collect_news(
    keywords: List[str],
    days: int = 7,
    feeds: List[Dict[str, str]] | None = None,
) -> List[Dict[str, Any]]:
    """
    Fetch articles from RSS feeds and return those published within *days* days
    that contain at least one keyword (case-insensitive) in title or summary.

    Args:
        keywords: list of search terms (e.g. ["Alzheimer", "amyloid"])
        days: look-back window in days
        feeds: list of {"name": ..., "url": ...}; defaults to RSS_FEEDS

    Returns:
        List of article dicts sorted newest-first.
    """
    if feeds is None:
        feeds = RSS_FEEDS

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    kw_patterns = [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]
    articles: List[Dict[str, Any]] = []

    for feed_meta in feeds:
        try:
            resp = requests.get(
                feed_meta["url"],
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": "HM-Intelligence/1.0 RSS Reader"},
            )
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except Exception as exc:
            logger.warning("Failed to fetch feed %s: %s", feed_meta["name"], exc)
            continue

        count = 0
        for entry in feed.entries:
            if count >= MAX_NEWS_PER_FEED:
                break

            pub_date = _parse_date(entry)
            if pub_date and pub_date < cutoff:
                continue  # too old

            title = _clean_html(entry.get("title", ""))
            summary = _clean_html(entry.get("summary", "") or entry.get("description", ""))
            full_text = f"{title} {summary}"

            if not any(p.search(full_text) for p in kw_patterns):
                continue

            articles.append(
                {
                    "source": feed_meta["name"],
                    "title": title,
                    "summary": summary[:600],  # truncate long summaries
                    "url": entry.get("link", ""),
                    "published": pub_date.strftime("%Y-%m-%d %H:%M UTC") if pub_date else "Unknown",
                    "published_dt": pub_date,
                }
            )
            count += 1

    # Sort newest first, unknown dates at the end
    articles.sort(
        key=lambda a: a["published_dt"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    # Remove the datetime object before returning (not JSON-serialisable)
    for a in articles:
        del a["published_dt"]

    logger.info("Collected %d articles matching keywords %s", len(articles), keywords)
    return articles
