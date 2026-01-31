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
                "content_html": html_content,
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


def generate_rss(pages):
    rss_items = []
    # Sort pages reverse chronological
    sorted_pages = sorted(pages, key=lambda x: x["date"], reverse=True)

    # Limit to latest 10 items
    sorted_pages = sorted_pages[:10]

    # Base URL for the site (Update this with your actual GitHub Pages URL)
    base_url = "https://ch2ohch2oh.github.io/wsbreporter"

    for page in sorted_pages:
        title = page["title"]
        link = f"{base_url}/{page['url']}"
        # RFC-822 date format
        pub_date = page["date"].strftime("%a, %d %b %Y 00:00:00 +0000")

        rss_items.append(f"""
        <item>
            <title>{title}</title>
            <link>{link}</link>
            <guid>{link}</guid>
            <pubDate>{pub_date}</pubDate>
            <description><![CDATA[{page["content_html"]}]]></description>
        </item>""")

    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<meta name="follow.it-verification-code" content="sy0DsFNYN9NFzQaK17GB"/>
<channel>
    <title>Hindsight Capital Management</title>
    <link>{base_url}</link>
    <description>Daily market summaries from r/wallstreetbets</description>
    <language>en-us</language>
    {"".join(rss_items)}
</channel>
</rss>"""

    output_path = os.path.join(HTML_DIR, "rss.xml")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rss_content)
    print(f"Generated rss.xml")


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


def generate_disclaimer(base_template):
    disclaimer_content = """
    <h1>Legal Disclaimer</h1>
    
    <p style="text-align: center; font-style: italic; margin-bottom: 30px;">Last Updated: January 31, 2026</p>
    
    <h2>AI-Generated Content Notice</h2>
    <p>The content on this website is generated using artificial intelligence (AI) technology. All summaries, analyses, and commentary are produced by automated systems and should be understood as such. The AI processes publicly available information from online forums and other sources, but does not verify the accuracy or reliability of such information.</p>
    
    <h2>Not Financial Advice</h2>
    <p>Nothing on this website constitutes financial, investment, legal, or professional advice. The content is provided for informational and entertainment purposes only. You should not rely on any information on this site as a basis for making financial or investment decisions. Always consult with qualified financial advisors, accountants, and legal professionals before making any investment decisions.</p>
    
    <h2>No Warranty or Guarantee</h2>
    <p>This website and its content are provided "as is" without any warranties of any kind, either express or implied. We make no representations or warranties regarding the accuracy, completeness, reliability, or timeliness of any content on this site. The AI-generated summaries may contain errors, omissions, or inaccuracies.</p>
    
    <h2>Limitation of Liability</h2>
    <p>To the fullest extent permitted by law, we disclaim all liability for any direct, indirect, incidental, consequential, or punitive damages arising from your use of this website or reliance on its content. This includes, but is not limited to, any financial losses, lost profits, or damages resulting from investment decisions made based on information found on this site.</p>
    
    <h2>Information Accuracy</h2>
    <p>While we strive to provide useful summaries, the AI system may misinterpret, misrepresent, or incorrectly summarize source material. Market data, stock prices, and other financial information may be outdated, incomplete, or inaccurate. Always verify information through official and authoritative sources before taking any action.</p>
    
    <h2>Third-Party Content</h2>
    <p>This website summarizes content from third-party sources, including online forums and social media. We do not endorse, verify, or take responsibility for the accuracy or reliability of such third-party content. The views and opinions expressed in the source material do not necessarily reflect our own views or opinions.</p>
    
    <h2>Investment Risks</h2>
    <p>Investing in financial markets involves substantial risk of loss. Past performance is not indicative of future results. The value of investments can go down as well as up, and you may lose some or all of your invested capital. Only invest money that you can afford to lose.</p>
    
    <h2>Use at Your Own Risk</h2>
    <p>By accessing and using this website, you acknowledge and agree that you do so at your own risk. You are solely responsible for any decisions you make based on the content provided on this site.</p>
    
    <h2>Changes to This Disclaimer</h2>
    <p>We reserve the right to modify this disclaimer at any time without prior notice. Your continued use of this website following any changes constitutes your acceptance of such changes.</p>
    
    <h2>Contact</h2>
    <p>If you have any questions about this disclaimer, please contact us through our GitHub repository.</p>
    
    <hr>
    
    <p style="text-align: center; margin-top: 40px;">
        <a href="index.html">Return to Latest Letter</a> • <a href="catalog.html">View All Letters</a>
    </p>
    """

    # Fill Base Template for Disclaimer
    page_html = (
        base_template.replace("{{SUBREDDIT}}", "wallstreetbets")
        .replace("{{DATE_YMD}}", datetime.now().strftime("%Y-%m-%d"))
        .replace("{{DATE_FULL}}", format_date(datetime.now()))
        .replace("{{CONTENT}}", disclaimer_content)
    )

    output_path = os.path.join(HTML_DIR, "disclaimer.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"Generated disclaimer.html")


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
    generate_rss(pages)
    generate_disclaimer(loaded_templates["base"])
    print("Site generation complete.")


if __name__ == "__main__":
    main()
