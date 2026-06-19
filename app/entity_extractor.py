"""AI-powered entity extraction from news articles using OpenAI."""
import json
import logging
from typing import Any, Dict, List

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = """\
You are a pharmaceutical and biotech intelligence analyst.
Extract structured information from the given news article.

Return ONLY valid JSON with this exact schema (no markdown, no explanation):
{
  "companies": ["company name", ...],
  "drugs": ["drug name or code", ...],
  "diseases": ["disease or indication", ...],
  "clinical_phases": ["Phase 1", "Phase 2", "Phase 3", "Approved", ...],
  "deal_types": ["partnership", "acquisition", "licensing", "investment", ...],
  "key_events": ["brief description of key event", ...],
  "sentiment": "positive" | "negative" | "neutral",
  "relevance_tags": ["competitive intelligence", "clinical trial", "regulatory", "deal", ...]
}

Rules:
- Include only entities explicitly mentioned in the text.
- Use standardised terms (e.g. "Alzheimer's Disease" not "AD").
- Return empty arrays [] if no entities are found.
- Keep key_events concise (≤15 words each).
"""


def extract_entities(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured entities from a single news article.

    Args:
        article: dict with keys 'title', 'summary', 'source', 'url'

    Returns:
        Original article dict enriched with an 'entities' key.
    """
    text = f"Title: {article.get('title', '')}\n\nSummary: {article.get('summary', '')}"

    try:
        response = _get_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=500,
        )
        raw = response.choices[0].message.content.strip()
        entities = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse error for article '%s': %s", article.get("title"), exc)
        entities = _empty_entities()
    except Exception as exc:
        logger.error("Entity extraction failed for article '%s': %s", article.get("title"), exc)
        entities = _empty_entities()

    return {**article, "entities": entities}


def extract_entities_batch(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract entities from a list of articles."""
    enriched = []
    for i, article in enumerate(articles):
        logger.debug("Extracting entities from article %d/%d", i + 1, len(articles))
        enriched.append(extract_entities(article))
    return enriched


def _empty_entities() -> Dict[str, Any]:
    return {
        "companies": [],
        "drugs": [],
        "diseases": [],
        "clinical_phases": [],
        "deal_types": [],
        "key_events": [],
        "sentiment": "neutral",
        "relevance_tags": [],
    }
