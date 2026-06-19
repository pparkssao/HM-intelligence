"""Orchestration: end-to-end pipeline from keywords → email report."""
import logging
from typing import Any, Dict, List

from app.news_collector import collect_news
from app.entity_extractor import extract_entities_batch
from app.pipeline_matcher import aggregate_matches
from app.insight_generator import generate_insights
from app.email_sender import send_report, render_report

logger = logging.getLogger(__name__)


def run_intelligence_pipeline(
    keywords: List[str],
    days: int,
    to_email: str | None = None,
    send_email: bool = True,
) -> Dict[str, Any]:
    """
    Full end-to-end intelligence pipeline.

    1. Collect news from RSS feeds
    2. Extract entities with AI
    3. Match against pipeline DB
    4. Generate strategic insights
    5. (Optional) Send email report

    Args:
        keywords: list of search keywords
        days: look-back window in days
        to_email: recipient email address
        send_email: whether to send the email

    Returns:
        Dict with keys: articles, pipeline, insights, html_report, email_sent
    """
    logger.info("Starting intelligence pipeline for keywords=%s days=%d", keywords, days)

    # Step 1: Collect news
    logger.info("Step 1/4 – Collecting news...")
    articles = collect_news(keywords=keywords, days=days)
    logger.info("  Found %d articles", len(articles))

    # Step 2: Extract entities
    logger.info("Step 2/4 – Extracting entities from %d articles...", len(articles))
    enriched_articles = extract_entities_batch(articles)

    # Step 3: Match pipeline
    logger.info("Step 3/4 – Matching pipeline DB...")
    pipeline_data = aggregate_matches(enriched_articles)
    logger.info(
        "  Found %d pipeline matches, %d companies mentioned",
        len(pipeline_data["pipeline_entries"]),
        len(pipeline_data["mentioned_companies"]),
    )

    # Step 4: Generate insights
    logger.info("Step 4/4 – Generating insights...")
    insights = generate_insights(
        keywords=keywords,
        articles=enriched_articles,
        pipeline_data=pipeline_data,
        days=days,
    )

    # Render HTML report
    html_report = render_report(
        keyword=", ".join(keywords),
        days=days,
        articles=enriched_articles,
        pipeline=pipeline_data,
        insights=insights,
    )

    # Step 5: Send email
    email_sent = False
    if send_email and to_email:
        logger.info("Sending report to %s...", to_email)
        email_sent = send_report(
            to_email=to_email,
            keyword=", ".join(keywords),
            days=days,
            articles=enriched_articles,
            pipeline=pipeline_data,
            insights=insights,
        )

    return {
        "articles": enriched_articles,
        "pipeline": pipeline_data,
        "insights": insights,
        "html_report": html_report,
        "email_sent": email_sent,
    }
