"""
HTML rendering for WSB summaries.
Converts markdown summaries to styled HTML.
"""

import argparse
import os
from datetime import datetime
import markdown
import re
import pytz


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

    # Extract date from markdown text or default to now
    # Look for "**Date:** {date_string}"
    date_match = re.search(r"\*\*Date:\*\*\s*(.+)", markdown_text)

    ny_tz = pytz.timezone("America/New_York")
    base_date = datetime.now(ny_tz)

    date_str = base_date.strftime("%B %d, %Y at %I:%M %p %Z")  # Default if not found

    if date_match:
        extracted_date = date_match.group(1).strip()
        try:
            # Try parsing with time: "February 01, 2026 at 02:45 PM EST"
            parsed_date = datetime.strptime(extracted_date, "%B %d, %Y at %I:%M %p %Z")
            date_str = parsed_date.strftime("%B %d, %Y at %I:%M %p %Z")
            base_date = parsed_date
        except ValueError:
            try:
                # Try parsing old format: "February 01, 2026"
                parsed_date = datetime.strptime(extracted_date, "%B %d, %Y")
                # If old format, just use the extracted string as is for the "Full Date" display
                date_str = extracted_date
                base_date = parsed_date  # This will have 00:00:00 time
            except ValueError:
                # If all parsing fails, fall back to current time (already set)
                pass

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(project_root, "templates", "report_template.html")

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        html_doc = template.replace("{{SUBREDDIT}}", subreddit)
        html_doc = html_doc.replace("{{DATE_YMD}}", base_date.strftime("%Y-%m-%d"))
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a Markdown report as HTML")
    parser.add_argument("input_file", help="Path to the input Markdown file")
    parser.add_argument(
        "-o", "--output", help="Path to the output HTML file (optional)"
    )
    parser.add_argument(
        "-s",
        "--subreddit",
        default="wallstreetbets",
        help="Subreddit name for the title (default: wallstreetbets)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        raise SystemExit(1)

    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            markdown_text = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        raise SystemExit(1)

    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(os.getcwd(), f"wsb_summary_{timestamp}.html")

    print(f"Rendering report for r/{args.subreddit}...")
    if save_html_report(markdown_text, output_path, args.subreddit):
        print(f"HTML report saved to: {output_path}")
    else:
        print("Failed to save HTML report")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
