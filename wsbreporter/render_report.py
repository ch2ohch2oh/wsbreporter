#!/usr/bin/env python3
"""
Stand-alone script to convert a local markdown file to an HTML report.
Useful for testing the HTML formatting without making API calls.

Usage:
    python3 render_report.py <input_file> [--output <output_file>] [--subreddit <subreddit>]
"""

import argparse
import os
import sys
from datetime import datetime

# Add parent directory to path so we can import wsbreporter modules
# In this workspace, `wsbreporter` seems to be the package name but the files are in `code/wsbreporter`.
# If run from `code/wsbreporter`, we should be able to import local modules directly if we treat it as a script,
# OR if we want to treat `wsbreporter` as a package, we need to be in the parent dir.
# Given `run.py` does: sys.path.insert(0, parent_dir)
# Let's import directly from local directory since we are inside the package.

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import html_formatter  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="Convert markdown summary to HTML report"
    )
    parser.add_argument("input_file", help="Path to the input markdown file")
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
        sys.exit(1)

    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Default to same directory as script with current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(os.getcwd(), f"wsb_summary_{timestamp}.html")

    print(f"Rendering report for r/{args.subreddit}...")

    if html_formatter.save_html_report(content, output_path, args.subreddit):
        print(f"✅ HTML report saved to: {output_path}")
    else:
        print("❌ Failed to save HTML report")
        sys.exit(1)


if __name__ == "__main__":
    main()
