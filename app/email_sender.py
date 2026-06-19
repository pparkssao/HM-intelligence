"""Email sending via SMTP with HTML report."""
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List
import os

from jinja2 import Environment, FileSystemLoader

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def render_report(
    keyword: str,
    days: int,
    articles: List[Dict[str, Any]],
    pipeline: Dict[str, Any],
    insights: Dict[str, Any],
) -> str:
    """Render the HTML email report from template."""
    env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR), autoescape=True)
    template = env.get_template("email_report.html")
    return template.render(
        keyword=keyword,
        days=days,
        articles=articles,
        pipeline=pipeline,
        insights=insights,
        news_count=len(articles),
        pipeline_count=len(pipeline.get("pipeline_entries", [])),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M KST"),
    )


def send_report(
    to_email: str,
    keyword: str,
    days: int,
    articles: List[Dict[str, Any]],
    pipeline: Dict[str, Any],
    insights: Dict[str, Any],
) -> bool:
    """
    Render and send the HTML report via SMTP.

    Returns:
        True if sent successfully, False otherwise.
    """
    html_body = render_report(keyword, days, articles, pipeline, insights)

    subject = (
        f"[HM Intelligence] {keyword} 경쟁사 동향 리포트 "
        f"({datetime.now().strftime('%Y.%m.%d')} 기준 최근 {days}일)"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, [to_email], msg.as_string())
        logger.info("Report sent to %s", to_email)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed – check SMTP_USER / SMTP_PASSWORD")
        return False
    except Exception as exc:
        logger.error("Failed to send email: %s", exc)
        return False
