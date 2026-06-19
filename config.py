"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Email / SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)

# News collection
DEFAULT_DAYS = int(os.getenv("DEFAULT_DAYS", "7"))
MAX_NEWS_PER_FEED = int(os.getenv("MAX_NEWS_PER_FEED", "20"))
REQUEST_TIMEOUT = 15  # seconds

# RSS feeds – pharmaceutical / biotech news sources
RSS_FEEDS = [
    {"name": "BioPharma Dive",    "url": "https://www.biopharmadive.com/feeds/news/"},
    {"name": "STAT News",         "url": "https://www.statnews.com/feed/"},
    {"name": "FiercePharma",      "url": "https://www.fiercepharma.com/rss/xml"},
    {"name": "FierceBiotech",     "url": "https://www.fiercebiotech.com/rss/xml"},
    {"name": "Endpoints News",    "url": "https://endpts.com/feed/"},
    {"name": "Reuters Health",    "url": "https://feeds.reuters.com/reuters/healthNews"},
    {"name": "MedPage Today",     "url": "https://www.medpagetoday.com/rss/headlines.xml"},
    {"name": "PharmaLive",        "url": "https://www.pharmalive.com/feed/"},
    {"name": "BioWorld",          "url": "https://www.bioworld.com/rss"},
    {"name": "PMLive",            "url": "https://www.pmlive.com/rss.aspx"},
]
