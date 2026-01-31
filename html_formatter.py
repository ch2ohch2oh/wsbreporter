"""
HTML formatter for WSB summaries.
Converts markdown summaries to styled HTML.
"""

from datetime import datetime
import markdown


def markdown_to_html(markdown_text: str, subreddit: str = "wallstreetbets") -> str:
    """
    Converts markdown summary to styled HTML.

    Args:
        markdown_text: The markdown formatted summary
        subreddit: The subreddit name for the title

    Returns:
        str: Complete HTML document with styling
    """
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_text, extensions=["extra", "nl2br"])

    # Get current date/time
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y at %I:%M %p")

    # Valid keys: {{SUBREDDIT}}, {{DATE_YMD}}, {{BASE_URL}}, {{CONTENT}}, {{DATE_FULL}}

    import os

    project_root = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(project_root, "templates", "report_template.html")

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        html_doc = template.replace("{{SUBREDDIT}}", subreddit)
        html_doc = html_doc.replace("{{DATE_YMD}}", now.strftime("%Y-%m-%d"))
        html_doc = html_doc.replace("{{CONTENT}}", html_content)
        html_doc = html_doc.replace("{{DATE_FULL}}", date_str)

    except FileNotFoundError:
        print(f"Error: Template file not found at {template_path}")
        # Fallback to simple HTML if template fails
        html_doc = (
            f"<html><body><h1>Error loading template</h1>{html_content}</body></html>"
        )

    return html_doc


def save_html_report(
    markdown_text: str, output_path: str, subreddit: str = "wallstreetbets"
) -> bool:
    """
    Saves the markdown summary as an HTML file.

    Args:
        markdown_text: The markdown formatted summary
        output_path: Path where to save the HTML file
        subreddit: The subreddit name

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        html = markdown_to_html(markdown_text, subreddit)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return True
    except Exception as e:
        print(f"Error saving HTML report: {e}")
        return False
