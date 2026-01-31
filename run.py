#!/usr/bin/env python3
"""
Entry point script for wsbreporter.
Run this with: python3 run.py
"""

if __name__ == "__main__":
    import sys
    import os
    import argparse

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Add parent directory to path so we can import wsbreporter
    parent_dir = os.path.dirname(script_dir)
    sys.path.insert(0, parent_dir)

    # Import config to get defaults
    from wsbreporter import config

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Fetch and summarize Reddit posts from r/wallstreetbets"
    )
    parser.add_argument(
        "-p",
        "--posts",
        type=int,
        default=config.NUM_POSTS_TO_FETCH,
        help=f"Number of posts to fetch (default: {config.NUM_POSTS_TO_FETCH})",
    )
    parser.add_argument(
        "-s",
        "--subreddit",
        type=str,
        default=config.SUBREDDIT_NAME,
        help=f"Subreddit to fetch from (default: {config.SUBREDDIT_NAME})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show individual posts for debugging",
    )
    parser.add_argument(
        "--sort",
        type=str,
        choices=["hot", "new", "top", "rising"],
        default="hot",
        help="How to sort posts: hot (trending), new (recent), top (all-time), rising (default: hot)",
    )
    parser.add_argument(
        "--skip-pinned",
        action="store_true",
        help="Skip pinned/stickied posts like weekly threads (default: include them)",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Save summary as HTML file (default: console output only)",
    )
    args = parser.parse_args()

    # Import and run
    from wsbreporter.main import main

    main(
        num_posts=args.posts,
        subreddit=args.subreddit,
        verbose=args.verbose,
        sort_by=args.sort,
        skip_pinned=args.skip_pinned,
        html_output=args.html,
    )
