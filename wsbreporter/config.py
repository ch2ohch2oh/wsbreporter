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

# Gemini API key (replace with your actual API key)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Subreddit to summarize
SUBREDDIT_NAME = "wallstreetbets"

# Number of top posts to fetch
NUM_POSTS_TO_FETCH = 25

# Number of top comments to fetch per post
NUM_COMMENTS_TO_FETCH = 20

# Output format: "plain" or "markdown"
OUTPUT_FORMAT = "markdown"

# Gemini Model Name
GEMINI_MODEL_NAME = "gemini-3-flash-preview"

# Path to the prompt template file (relative to project root)
PROMPT_TEMPLATE_PATH = "templates/prompt_template_hindsight.txt"
