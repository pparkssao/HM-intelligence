"""Pipeline database loading and matching."""
import logging
import os
import re
from typing import Any, Dict, List

import pandas as pd

from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pipeline_db.csv")


def load_pipeline_db(path: str = _DB_PATH) -> pd.DataFrame:
    """Load the pipeline CSV into a DataFrame."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def _normalise(text: str) -> str:
    """Lowercase and strip punctuation for fuzzy matching."""
    return re.sub(r"[^a-z0-9 ]", "", text.lower())


def _word_boundary_match(term: str, text: str) -> bool:
    """Return True if *term* appears as a whole-word sequence in *text*."""
    pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
    return bool(re.search(pattern, text))


def match_pipeline(
    entities: Dict[str, Any],
    db: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """
    Find pipeline entries that match any extracted entity
    (company, drug, or disease).

    Matching uses word-boundary checks to avoid false positives from
    partial substring overlaps (e.g. "phase" matching "phases").

    Args:
        entities: dict returned by entity_extractor (companies, drugs, diseases)
        db: pipeline DataFrame

    Returns:
        List of matching pipeline row dicts (deduplicated).
    """
    candidate_terms = (
        [_normalise(c) for c in entities.get("companies", [])]
        + [_normalise(d) for d in entities.get("drugs", [])]
        + [_normalise(dis) for dis in entities.get("diseases", [])]
    )

    # Filter out very short tokens that are too ambiguous
    candidate_terms = [t for t in candidate_terms if len(t) >= 4]

    if not candidate_terms:
        return []

    matched_rows = []
    for _, row in db.iterrows():
        row_text = _normalise(
            f"{row.get('company', '')} {row.get('drug_name', '')} {row.get('indication', '')}"
        )
        if any(
            _word_boundary_match(term, row_text) or _word_boundary_match(row_text, term)
            for term in candidate_terms
        ):
            matched_rows.append(row.to_dict())

    # Deduplicate by (company, drug_name)
    seen = set()
    unique = []
    for r in matched_rows:
        key = (r.get("company", ""), r.get("drug_name", ""))
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique


def aggregate_matches(enriched_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate all pipeline matches across a list of enriched articles.

    Returns:
        {
          "pipeline_entries": [...],          # deduplicated pipeline rows
          "mentioned_companies": [...],        # unique companies from news
          "matched_companies": [...],          # companies in both news & pipeline DB
        }
    """
    db = load_pipeline_db()

    all_pipeline: List[Dict[str, Any]] = []
    all_companies: set = set()

    for article in enriched_articles:
        entities = article.get("entities", {})
        for c in entities.get("companies", []):
            all_companies.add(c)
        matches = match_pipeline(entities, db)
        all_pipeline.extend(matches)

    # Deduplicate pipeline entries
    seen = set()
    unique_pipeline = []
    for entry in all_pipeline:
        key = (entry.get("company", ""), entry.get("drug_name", ""))
        if key not in seen:
            seen.add(key)
            unique_pipeline.append(entry)

    matched_companies = sorted(
        {e.get("company", "") for e in unique_pipeline} & all_companies
    )

    return {
        "pipeline_entries": unique_pipeline,
        "mentioned_companies": sorted(all_companies),
        "matched_companies": matched_companies,
    }
