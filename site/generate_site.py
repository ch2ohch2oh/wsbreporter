import os
import sys

# Hack: Remove the script directory from sys.path to avoid shadowing the 'markdown' library
# by the local 'site/markdown' directory.
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    # We remove it from the start of the list where python adds it by default
    sys.path = [p for p in sys.path if p != script_dir]

import glob
import markdown
from datetime import datetime

# Define paths
BASE_DIR = script_dir  # We can use the captured script_dir
PROJECT_ROOT = os.path.dirname(BASE_DIR)
MARKDOWN_DIR = os.path.join(BASE_DIR, "markdown")
HTML_DIR = os.path.join(PROJECT_ROOT, "_site")
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "templates", "report_template.html")


def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


def read_template(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_markdown_files(path):
    files = glob.glob(os.path.join(path, "*.md"))

    valid_files = []
    for f in files:
        basename = os.path.basename(f)
        filename_no_ext = os.path.splitext(basename)[0]
        try:
            datetime.strptime(filename_no_ext, "%Y-%m-%d")
            valid_files.append(f)
        except ValueError:
            print(f"Skipping non-date file: {basename}")

    # Sort by filename (assuming YYYY-MM-DD.md format)
    return sorted(valid_files)


def parse_date_from_filename(filename):
    basename = os.path.basename(filename)
    date_str = os.path.splitext(basename)[0]
    return datetime.strptime(date_str, "%Y-%m-%d")


def format_date(dt):
    # e.g., "January 30, 2026"
    return dt.strftime("%B %d, %Y")


def generate_navigation(prev_file, next_file, nav_template, catalog_url="catalog.html"):
    nav_links = []

    if prev_file:
        prev_date = parse_date_from_filename(prev_file)
        prev_url = f"{prev_date.strftime('%Y-%m-%d')}.html"
        nav_links.append(f'<a href="{prev_url}">Previous</a>')
    else:
        nav_links.append('<span style="color: grey;">Previous</span>')

    nav_links.append(f'<a href="{catalog_url}">Catalog</a>')

    if next_file:
        next_date = parse_date_from_filename(next_file)
        next_url = f"{next_date.strftime('%Y-%m-%d')}.html"
        nav_links.append(f'<a href="{next_url}">Next</a>')
    else:
        nav_links.append('<span style="color: grey;">Next</span>')

    return nav_template.replace("{{NAV_LINKS}}", " | ".join(nav_links))


def convert_markdown_to_html(content):
    return markdown.markdown(content, extensions=["extra", "nl2br"])


def extract_title(content):
    import re

    match = re.search(r"\*\*Subject:\*\*\s*(.*)", content)
    if match:
        return match.group(1).strip()
    return "Market Summary"


def generate_pages(markdown_files, base_template, inner_template, nav_template):
    ensure_directory(HTML_DIR)

    generated_pages = []

    for i, md_file in enumerate(markdown_files):
        prev_file = markdown_files[i - 1] if i > 0 else None
        next_file = markdown_files[i + 1] if i < len(markdown_files) - 1 else None

        with open(md_file, "r", encoding="utf-8") as f:
            md_content = f.read()

        file_date = parse_date_from_filename(md_file)
        full_date_str = format_date(file_date)
        title = extract_title(md_content)
        html_content = convert_markdown_to_html(md_content)

        # Navigation
        nav_html = generate_navigation(prev_file, next_file, nav_template)

        # Main content
        full_content = (
            inner_template.replace("{{NAV_TOP}}", nav_html)
            .replace("{{LETTER_CONTENT}}", html_content)
            .replace("{{NAV_BOTTOM}}", nav_html)
        )

        # Fill Base Template
        page_html = (
            base_template.replace("{{SUBREDDIT}}", "wallstreetbets")
            .replace("{{DATE_YMD}}", file_date.strftime("%Y-%m-%d"))
            .replace("{{DATE_FULL}}", full_date_str)
            .replace("{{CONTENT}}", full_content)
        )

        output_filename = f"{file_date.strftime('%Y-%m-%d')}.html"
        output_path = os.path.join(HTML_DIR, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(page_html)

        generated_pages.append(
            {
                "date": file_date,
                "url": output_filename,
                "title": title,
                "display_date": full_date_str,
            }
        )
        print(f"Generated {output_filename}")

    return generated_pages


def generate_catalog(pages, base_template, inner_template):
    # Sort pages reverse chronological for catalog
    sorted_pages = sorted(pages, key=lambda x: x["date"], reverse=True)

    catalog_items = []
    for page in sorted_pages:
        # Format: "January 30, 2026 - The Subject Line"
        link_text = f"{page['display_date']} - {page['title']}"
        catalog_items.append(f'<li><a href="{page["url"]}">{link_text}</a></li>')

    catalog_content = inner_template.replace(
        "{{CATALOG_ITEMS}}", "".join(catalog_items)
    )

    # Fill Base Template for Catalog
    page_html = (
        base_template.replace("{{SUBREDDIT}}", "wallstreetbets")
        .replace("{{DATE_YMD}}", datetime.now().strftime("%Y-%m-%d"))
        .replace("{{DATE_FULL}}", format_date(datetime.now()))
        .replace("{{CONTENT}}", catalog_content)
    )

    output_path = os.path.join(HTML_DIR, "catalog.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"Generated catalog.html")


def generate_redirect_index(pages):
    if not pages:
        return

    # Sort pages to find the latest
    sorted_pages = sorted(pages, key=lambda x: x["date"], reverse=True)
    latest_page = sorted_pages[0]
    latest_url = latest_page["url"]

    redirect_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url={latest_url}" />
    <title>Redirecting...</title>
</head>
<body>
    <p>Redirecting to latest letter: <a href="{latest_url}">{latest_url}</a></p>
</body>
</html>'''

    output_path = os.path.join(HTML_DIR, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(redirect_html)
    print(f"Generated index.html (redirect to {latest_url})")


def main():
    print("Starting site generation...")

    # Template paths
    templates = {
        "base": TEMPLATE_PATH,
        "letter": os.path.join(BASE_DIR, "templates", "letter_inner.html"),
        "catalog": os.path.join(BASE_DIR, "templates", "catalog_inner.html"),
        "nav": os.path.join(BASE_DIR, "templates", "nav.html"),
    }

    # Verify templates exist
    for name, path in templates.items():
        if not os.path.exists(path):
            print(f"Error: Template '{name}' not found at {path}")
            sys.exit(1)

    # Read templates
    loaded_templates = {name: read_template(path) for name, path in templates.items()}

    markdown_files = get_markdown_files(MARKDOWN_DIR)

    if not markdown_files:
        print("No markdown files found.")
        sys.exit(0)

    pages = generate_pages(
        markdown_files,
        loaded_templates["base"],
        loaded_templates["letter"],
        loaded_templates["nav"],
    )
    generate_catalog(pages, loaded_templates["base"], loaded_templates["catalog"])
    generate_redirect_index(pages)
    print("Site generation complete.")


if __name__ == "__main__":
    main()
