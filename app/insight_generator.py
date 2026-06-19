"""AI-powered insight generation combining news and pipeline data."""
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


INSIGHT_SYSTEM_PROMPT = """\
You are a pharmaceutical competitive intelligence analyst at Hanmi Pharmaceutical.
Your role is to interpret news and pipeline data to generate actionable strategic insights.

Respond in the following JSON schema ONLY (no markdown):
{
  "executive_summary": "2-3 sentence summary of the most important developments",
  "key_insights": [
    {
      "title": "Insight title",
      "detail": "Detailed explanation (2-4 sentences)",
      "implication_for_hanmi": "Direct strategic implication for Hanmi Pharmaceutical",
      "urgency": "high" | "medium" | "low"
    }
  ],
  "competitive_landscape": "Overview of competitive dynamics in this therapeutic area",
  "opportunities": ["Specific opportunity for Hanmi", ...],
  "risks": ["Specific risk or threat for Hanmi", ...],
  "recommended_actions": ["Concrete next step", ...]
}

Guidelines:
- Focus on competitive intelligence relevant to Korean pharma (especially Hanmi).
- Be specific about clinical phases, companies, and market implications.
- Keep insights actionable, not generic.
- If pipeline data is available, reference specific drugs and stages.
- Respond in Korean (한국어).
"""


def generate_insights(
    keywords: List[str],
    articles: List[Dict[str, Any]],
    pipeline_data: Dict[str, Any],
    days: int,
) -> Dict[str, Any]:
    """
    Generate strategic insights from collected news and pipeline matches.

    Args:
        keywords: search keywords used
        articles: enriched article list (with entities)
        pipeline_data: output of pipeline_matcher.aggregate_matches()
        days: look-back window

    Returns:
        Insight dict matching INSIGHT_SYSTEM_PROMPT schema.
    """
    # Build a compact context payload for the prompt
    news_digest = []
    for a in articles[:15]:  # limit to top 15 articles
        news_digest.append(
            {
                "title": a.get("title"),
                "source": a.get("source"),
                "published": a.get("published"),
                "key_events": a.get("entities", {}).get("key_events", []),
                "companies": a.get("entities", {}).get("companies", []),
                "drugs": a.get("entities", {}).get("drugs", []),
                "diseases": a.get("entities", {}).get("diseases", []),
                "clinical_phases": a.get("entities", {}).get("clinical_phases", []),
            }
        )

    pipeline_digest = []
    for p in pipeline_data.get("pipeline_entries", [])[:20]:
        pipeline_digest.append(
            {
                "company": p.get("company"),
                "drug": p.get("drug_name"),
                "indication": p.get("indication"),
                "phase": p.get("phase"),
                "mechanism": p.get("mechanism"),
            }
        )

    user_content = f"""
분석 키워드: {', '.join(keywords)}
조회 기간: 최근 {days}일
뉴스 기사 수: {len(articles)}개
매칭된 파이프라인 항목: {len(pipeline_data.get('pipeline_entries', []))}개

== 뉴스 요약 ==
{json.dumps(news_digest, ensure_ascii=False, indent=2)}

== 관련 파이프라인 현황 ==
{json.dumps(pipeline_digest, ensure_ascii=False, indent=2)}

== 언급된 회사 ==
{', '.join(pipeline_data.get('mentioned_companies', []))}
"""

    try:
        response = _get_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": INSIGHT_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Insight JSON parse error: %s", exc)
        return _empty_insights()
    except Exception as exc:
        logger.error("Insight generation failed: %s", exc)
        return _empty_insights()


def _empty_insights() -> Dict[str, Any]:
    return {
        "executive_summary": "인사이트를 생성할 수 없습니다. API 키 및 설정을 확인해 주세요.",
        "key_insights": [],
        "competitive_landscape": "",
        "opportunities": [],
        "risks": [],
        "recommended_actions": [],
    }
