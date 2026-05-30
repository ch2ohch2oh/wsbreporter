# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Reddit API credentials (replace with your actual credentials)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv(
    "REDDIT_USER_AGENT"
)  # A unique string to identify your application

# LLM provider. Supported values: gemini, deepseek, openai, openai-compatible
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

# Gemini settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3-flash-preview")

# DeepSeek settings. DeepSeek exposes an OpenAI-compatible API.
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL_NAME = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

# Generic OpenAI-compatible settings for other providers.
OPENAI_COMPATIBLE_API_KEY = os.getenv("OPENAI_COMPATIBLE_API_KEY")
OPENAI_COMPATIBLE_BASE_URL = os.getenv("OPENAI_COMPATIBLE_BASE_URL")
OPENAI_COMPATIBLE_MODEL_NAME = os.getenv("OPENAI_COMPATIBLE_MODEL_NAME")

# Subreddit to summarize
SUBREDDIT_NAME = "wallstreetbets"

# Number of top posts to fetch
NUM_POSTS_TO_FETCH = 25

# Number of top comments to fetch per post
NUM_COMMENTS_TO_FETCH = 50

# Number of stored comments per post to include in the LLM report context.
REPORT_COMMENTS_PER_POST = int(os.getenv("REPORT_COMMENTS_PER_POST", "12"))

# Max words from a post body/comment body included in the LLM report context.
REPORT_MAX_BODY_WORDS = int(os.getenv("REPORT_MAX_BODY_WORDS", "220"))

# Refresh comments for an already-seen post after this many hours.
COMMENT_REFRESH_HOURS = int(os.getenv("COMMENT_REFRESH_HOURS", "2"))

# Path to the prompt template file (relative to project root)
PROMPT_TEMPLATE_PATH = "templates/prompt_template_hindsight_v2.txt"
EDITOR_PROMPT_TEMPLATE_PATH = os.getenv(
    "EDITOR_PROMPT_TEMPLATE_PATH", "templates/prompt_template_editor.txt"
)
REPORT_EDIT_PASS = os.getenv("REPORT_EDIT_PASS", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Optional external news context. The first provider uses public RSS feeds and
# caches fetched items in SQLite.
REPORT_WITH_NEWS = os.getenv("REPORT_WITH_NEWS", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
NEWS_MAX_TERMS = int(os.getenv("NEWS_MAX_TERMS", "8"))
NEWS_ITEMS_PER_TERM = int(os.getenv("NEWS_ITEMS_PER_TERM", "3"))
NEWS_PROVIDER = os.getenv("NEWS_PROVIDER", "google-news-rss")

# SQLite database path. Relative paths are resolved from the project root.
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/wsbreporter.sqlite3")


def get_llm_model_name() -> str | None:
    if LLM_PROVIDER == "gemini":
        return GEMINI_MODEL_NAME
    if LLM_PROVIDER == "deepseek":
        return DEEPSEEK_MODEL_NAME
    if LLM_PROVIDER == "openai":
        return OPENAI_MODEL_NAME
    if LLM_PROVIDER == "openai-compatible":
        return OPENAI_COMPATIBLE_MODEL_NAME
    return None


def get_llm_api_key() -> str | None:
    if LLM_PROVIDER == "gemini":
        return GEMINI_API_KEY
    if LLM_PROVIDER == "deepseek":
        return DEEPSEEK_API_KEY
    if LLM_PROVIDER == "openai":
        return OPENAI_API_KEY
    if LLM_PROVIDER == "openai-compatible":
        return OPENAI_COMPATIBLE_API_KEY
    return None


def get_llm_base_url() -> str | None:
    if LLM_PROVIDER == "deepseek":
        return DEEPSEEK_BASE_URL
    if LLM_PROVIDER == "openai":
        return OPENAI_BASE_URL
    if LLM_PROVIDER == "openai-compatible":
        return OPENAI_COMPATIBLE_BASE_URL
    return None


def get_llm_display_name() -> str:
    model_name = get_llm_model_name()
    if model_name:
        return f"{LLM_PROVIDER}:{model_name}"
    return LLM_PROVIDER
