from . import config
from . import reporter
from . import scraper


def run_pipeline(
    num_posts=None,
    subreddit=None,
    verbose=False,
    sort_by="hot",
    skip_pinned=False,
    html_output=False,
    output_file=None,
    markdown_output_file=None,
    dry_run=False,
    edit_pass=None,
    with_news=None,
):
    num_posts = num_posts or config.NUM_POSTS_TO_FETCH
    subreddit = subreddit or config.SUBREDDIT_NAME

    posts = scraper.scrape_posts(
        num_posts=num_posts,
        subreddit=subreddit,
        sort_by=sort_by,
        skip_pinned=skip_pinned,
    )
    if not posts:
        return None

    return reporter.generate_report(
        posts=posts,
        num_posts=num_posts,
        subreddit=subreddit,
        verbose=verbose,
        html_output=html_output,
        output_file=output_file,
        markdown_output_file=markdown_output_file,
        dry_run=dry_run,
        edit_pass=edit_pass,
        with_news=with_news,
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape Reddit posts and generate a WSB report"
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
        help="How to sort posts: hot, new, top, rising (default: hot)",
    )
    parser.add_argument(
        "--skip-pinned",
        action="store_true",
        help="Skip pinned/stickied posts like weekly threads",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Save summary as HTML file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Custom output filename for the HTML report",
    )
    parser.add_argument(
        "-mo",
        "--markdown-output",
        type=str,
        help="Custom output filename for the Markdown report",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the LLM input after scraping without calling the LLM",
    )
    parser.add_argument(
        "--edit-pass",
        action="store_true",
        default=config.REPORT_EDIT_PASS,
        help="Run a second LLM editor pass before saving the report",
    )
    parser.add_argument(
        "--with-news",
        action="store_true",
        default=config.REPORT_WITH_NEWS,
        help="Fetch and include cached external news context",
    )
    args = parser.parse_args()

    run_pipeline(
        num_posts=args.posts,
        subreddit=args.subreddit,
        verbose=args.verbose,
        sort_by=args.sort,
        skip_pinned=args.skip_pinned,
        html_output=args.html,
        output_file=args.output,
        markdown_output_file=args.markdown_output,
        dry_run=args.dry_run,
        edit_pass=args.edit_pass,
        with_news=args.with_news,
    )


if __name__ == "__main__":
    main()
