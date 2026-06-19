"""HM Intelligence – Streamlit Frontend."""
import logging
import re
import sys
import os

import streamlit as st
import pandas as pd

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(__file__))

from app.main import run_intelligence_pipeline
from config import OPENAI_API_KEY, SMTP_USER

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="HM Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .hm-header {
        background: linear-gradient(135deg, #003087 0%, #0057b8 100%);
        padding: 24px 32px;
        border-radius: 10px;
        margin-bottom: 24px;
        color: white;
    }
    .hm-header h1 { margin: 0 0 6px; font-size: 28px; }
    .hm-header p  { margin: 0; opacity: 0.8; font-size: 14px; }
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px 20px;
        text-align: center;
    }
    .metric-card .value { font-size: 32px; font-weight: 700; color: #003087; }
    .metric-card .label { font-size: 12px; color: #718096; margin-top: 4px; }
    .insight-box {
        background: #f0f6ff;
        border-left: 4px solid #003087;
        padding: 16px 20px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 12px;
    }
    .urgency-high   { color: #c0392b; font-weight: 700; }
    .urgency-medium { color: #e67e22; font-weight: 700; }
    .urgency-low    { color: #27ae60; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar – inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Hanmi_Pharmaceutical_logo.svg/640px-Hanmi_Pharmaceutical_logo.svg.png",
        width=180,
    ) if False else st.markdown("## 📊 HM Intelligence")

    st.markdown("---")
    st.markdown("### 🔍 검색 설정")

    keyword_input = st.text_input(
        "키워드 (쉼표로 구분)",
        value="Alzheimer",
        help="예: Alzheimer, amyloid, lecanemab",
    )
    days = st.slider(
        "조회 기간 (일)",
        min_value=1,
        max_value=30,
        value=7,
        step=1,
    )

    st.markdown("---")
    st.markdown("### 📧 이메일 설정")

    to_email = st.text_input(
        "수신 이메일",
        value="",
        placeholder="xxx@hanmi.com",
    )
    send_email = st.checkbox("리포트 이메일 발송", value=False)

    st.markdown("---")
    st.markdown("### ⚙️ API 설정")

    api_key_input = st.text_input(
        "OpenAI API Key",
        type="password",
        value=OPENAI_API_KEY or "",
        help="환경변수 OPENAI_API_KEY 또는 여기에 직접 입력",
    )

    if api_key_input:
        os.environ["OPENAI_API_KEY"] = api_key_input
        import config as _cfg
        _cfg.OPENAI_API_KEY = api_key_input

    run_btn = st.button("🚀 분석 시작", type="primary", use_container_width=True)

    st.markdown("---")
    st.caption(
        "HM Intelligence v1.0  \n"
        "AI 기반 제약/바이오 경쟁 인텔리전스 플랫폼  \n"
        "© 2025 Hanmi Pharmaceutical"
    )

# ---------------------------------------------------------------------------
# Main area – header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hm-header">
      <h1>📊 HM Intelligence</h1>
      <p>키워드 기반 제약/바이오 뉴스 × 파이프라인 연결 → 경쟁사 R&D 동향 자동 분석</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# How it works (shown when no run has started)
# ---------------------------------------------------------------------------
if "result" not in st.session_state:
    c1, c2, c3, c4 = st.columns(4)
    for col, icon, title, desc in [
        (c1, "📡", "1. 뉴스 수집", "10개 RSS 피드에서\n실시간 수집"),
        (c2, "🤖", "2. AI 분석", "GPT-4가 회사·약물·\n임상단계 추출"),
        (c3, "🧬", "3. 파이프라인 매칭", "뉴스 ↔ 파이프라인 DB\n자동 연결"),
        (c4, "💡", "4. 인사이트 생성", "경쟁 환경·기회·리스크\n자동 요약 → 이메일"),
    ]:
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                  <div style="font-size:36px;">{icon}</div>
                  <div style="font-weight:700;margin:8px 0 4px;">{title}</div>
                  <div style="font-size:12px;color:#718096;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.info("👈 왼쪽 사이드바에서 키워드와 설정을 입력하고 **🚀 분석 시작** 버튼을 누르세요.")

# ---------------------------------------------------------------------------
# Run pipeline
# ---------------------------------------------------------------------------
if run_btn:
    if not api_key_input:
        st.error("⚠️ OpenAI API Key를 입력해 주세요.")
        st.stop()

    if send_email and not to_email:
        st.warning("⚠️ 이메일을 발송하려면 수신 이메일을 입력해 주세요.")

    keywords = [kw.strip() for kw in keyword_input.split(",") if kw.strip()]
    if not keywords:
        st.error("키워드를 입력해 주세요.")
        st.stop()

    with st.spinner("🔄 분석 중입니다. 잠시만 기다려 주세요..."):
        progress = st.progress(0, text="뉴스 수집 중...")

        # Patch entity extractor to use new API key
        import app.entity_extractor as _ee
        import app.insight_generator as _ig
        _ee._client = None
        _ig._client = None

        try:
            progress.progress(10, text="📡 뉴스 수집 중...")
            from app.news_collector import collect_news
            articles_raw = collect_news(keywords=keywords, days=days)

            progress.progress(35, text=f"🤖 AI 엔티티 추출 중... ({len(articles_raw)}건)")
            from app.entity_extractor import extract_entities_batch
            enriched_articles = extract_entities_batch(articles_raw)

            progress.progress(60, text="🧬 파이프라인 매칭 중...")
            from app.pipeline_matcher import aggregate_matches
            pipeline_data = aggregate_matches(enriched_articles)

            progress.progress(80, text="💡 인사이트 생성 중...")
            from app.insight_generator import generate_insights
            insights = generate_insights(
                keywords=keywords,
                articles=enriched_articles,
                pipeline_data=pipeline_data,
                days=days,
            )

            progress.progress(95, text="📧 이메일 준비 중...")
            from app.email_sender import render_report, send_report
            html_report = render_report(
                keyword=", ".join(keywords),
                days=days,
                articles=enriched_articles,
                pipeline=pipeline_data,
                insights=insights,
            )

            email_sent = False
            if send_email and to_email:
                email_sent = send_report(
                    to_email=to_email,
                    keyword=", ".join(keywords),
                    days=days,
                    articles=enriched_articles,
                    pipeline=pipeline_data,
                    insights=insights,
                )

            progress.progress(100, text="✅ 완료!")

            st.session_state["result"] = {
                "articles": enriched_articles,
                "pipeline": pipeline_data,
                "insights": insights,
                "html_report": html_report,
                "email_sent": email_sent,
                "keywords": keywords,
                "days": days,
            }

        except Exception as exc:
            st.error(f"오류가 발생했습니다: {exc}")
            st.exception(exc)
            st.stop()

# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------
if "result" in st.session_state:
    res = st.session_state["result"]
    articles = res["articles"]
    pipeline = res["pipeline"]
    insights = res["insights"]
    keywords = res["keywords"]
    days = res["days"]

    # Metrics row
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📰 수집 뉴스", len(articles))
    m2.metric("🏢 언급 회사", len(pipeline.get("mentioned_companies", [])))
    m3.metric("🧬 파이프라인 매칭", len(pipeline.get("pipeline_entries", [])))
    m4.metric("💊 관련 약물",
              len({p.get("drug_name") for p in pipeline.get("pipeline_entries", [])}))
    m5.metric("📧 이메일", "발송 완료 ✅" if res.get("email_sent") else "미발송")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["💡 인사이트", "📰 뉴스", "🧬 파이프라인", "📧 이메일 미리보기", "📋 원시 데이터"]
    )

    # ------------------------------------------------------------------
    # TAB 1 – Insights
    # ------------------------------------------------------------------
    with tab1:
        st.subheader("🔷 Executive Summary")
        st.info(insights.get("executive_summary", "—"))

        if insights.get("competitive_landscape"):
            st.subheader("🗺️ 경쟁 환경 분석")
            st.write(insights["competitive_landscape"])

        col_left, col_right = st.columns(2)
        with col_left:
            if insights.get("opportunities"):
                st.subheader("✅ 기회 요인")
                for opp in insights["opportunities"]:
                    st.success(f"• {opp}")

            if insights.get("recommended_actions"):
                st.subheader("📌 권고 액션")
                for action in insights["recommended_actions"]:
                    st.info(f"• {action}")

        with col_right:
            if insights.get("risks"):
                st.subheader("⚠️ 리스크 요인")
                for risk in insights["risks"]:
                    st.error(f"• {risk}")

        if insights.get("key_insights"):
            st.subheader("🎯 핵심 인사이트")
            for insight in insights["key_insights"]:
                urgency = insight.get("urgency", "low")
                urgency_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(urgency, "⚪")
                with st.expander(f"{urgency_emoji} {insight.get('title', '—')} [{urgency.upper()}]"):
                    st.write(insight.get("detail", ""))
                    if insight.get("implication_for_hanmi"):
                        st.markdown(
                            f"**🏢 한미 시사점:** {insight['implication_for_hanmi']}"
                        )

    # ------------------------------------------------------------------
    # TAB 2 – News
    # ------------------------------------------------------------------
    with tab2:
        st.subheader(f"최근 {days}일 뉴스 ({len(articles)}건)")
        for article in articles:
            entities = article.get("entities", {})
            sentiment = entities.get("sentiment", "neutral")
            s_emoji = {"positive": "📈", "negative": "📉", "neutral": "📊"}.get(sentiment, "📊")

            with st.expander(f"{s_emoji} [{article.get('source','?')}] {article.get('title','—')}"):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.caption(article.get("published", ""))
                    st.write(article.get("summary", ""))
                    if article.get("url"):
                        st.markdown(f"[🔗 원문 보기]({article['url']})")
                with col_b:
                    if entities.get("companies"):
                        st.markdown("**🏢 회사**")
                        for c in entities["companies"][:5]:
                            st.markdown(f"- {c}")
                    if entities.get("drugs"):
                        st.markdown("**💊 약물**")
                        for d in entities["drugs"][:5]:
                            st.markdown(f"- {d}")
                    if entities.get("clinical_phases"):
                        st.markdown("**📋 임상단계**")
                        for ph in entities["clinical_phases"][:3]:
                            st.markdown(f"- {ph}")

    # ------------------------------------------------------------------
    # TAB 3 – Pipeline
    # ------------------------------------------------------------------
    with tab3:
        st.subheader(f"매칭된 파이프라인 ({len(pipeline.get('pipeline_entries', []))}건)")

        if pipeline.get("mentioned_companies"):
            st.markdown(
                "**뉴스에 언급된 회사:** "
                + " · ".join(f"`{c}`" for c in pipeline["mentioned_companies"])
            )

        entries = pipeline.get("pipeline_entries", [])
        if entries:
            df = pd.DataFrame(entries)
            cols = ["company", "drug_name", "indication", "phase", "mechanism", "modality", "status", "region"]
            existing_cols = [c for c in cols if c in df.columns]
            st.dataframe(
                df[existing_cols],
                use_container_width=True,
                height=min(400, 40 + len(df) * 35),
            )

            # Phase breakdown chart
            if "phase" in df.columns:
                phase_counts = df["phase"].value_counts()
                st.bar_chart(phase_counts)
        else:
            st.info("파이프라인 DB에서 매칭된 항목이 없습니다. 키워드를 변경해 보세요.")

    # ------------------------------------------------------------------
    # TAB 4 – Email preview
    # ------------------------------------------------------------------
    with tab4:
        st.subheader("이메일 미리보기")
        if res.get("email_sent"):
            st.success(f"✅ 이메일이 발송되었습니다.")
        html_report = res.get("html_report", "")
        if html_report:
            st.download_button(
                "⬇️ HTML 리포트 다운로드",
                data=html_report,
                file_name=f"hm_intelligence_{keywords[0]}_{days}d.html",
                mime="text/html",
            )
            st.components.v1.html(html_report, height=800, scrolling=True)

    # ------------------------------------------------------------------
    # TAB 5 – Raw data
    # ------------------------------------------------------------------
    with tab5:
        st.subheader("원시 데이터")
        import json
        with st.expander("📰 뉴스 JSON"):
            st.json(articles[:5])  # show first 5
        with st.expander("🧬 파이프라인 JSON"):
            st.json(pipeline)
        with st.expander("💡 인사이트 JSON"):
            st.json(insights)

    # Re-run button
    st.markdown("---")
    if st.button("🔄 새로 분석하기"):
        del st.session_state["result"]
        st.rerun()
