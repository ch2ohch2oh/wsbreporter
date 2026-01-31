from . import reddit_client
from . import summarizer
from . import output_formatter
from . import html_formatter
from . import config
import argparse
from datetime import datetime
import os


def main(
    num_posts=None,
    subreddit=None,
    verbose=False,
    sort_by="hot",
    skip_pinned=False,
    html_output=False,
):
    # Use provided arguments or fall back to config defaults
    num_posts = num_posts or config.NUM_POSTS_TO_FETCH
    subreddit = subreddit or config.SUBREDDIT_NAME

    # Ensure API keys are set
    if (
        config.REDDIT_CLIENT_ID == "YOUR_REDDIT_CLIENT_ID"
        or config.REDDIT_CLIENT_SECRET == "YOUR_REDDIT_CLIENT_SECRET"
        or config.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY"
    ):
        print(
            "Error: Please update your API keys in wsbreporter/config.py before running."
        )
        return

    sort_label = sort_by if sort_by != "hot" else "hot (trending)"
    skip_label = " (skipping pinned)" if skip_pinned else ""
    print(f"Fetching {num_posts} {sort_label} posts from r/{subreddit}{skip_label}...")
    posts = reddit_client.fetch_top_posts(
        num_posts=num_posts,
        subreddit=subreddit,
        sort_by=sort_by,
        skip_pinned=skip_pinned,
    )

    if not posts:
        print(
            "Failed to fetch Reddit posts. Please check your network connection or API credentials."
        )
        return

    print(
        f"Successfully fetched {len(posts)} posts. Aggregating content for summarization..."
    )
    all_posts_content = ""
    for i, post in enumerate(posts):
        # Mark pinned posts so AI can treat them differently
        pinned_marker = "[PINNED] " if post.get("is_pinned", False) else ""
        post_header = f"--- Post {i + 1}: {pinned_marker}{post['title']} ---"
        all_posts_content += post_header + "\n"
        all_posts_content += f"Source URL: {post['url']}\n"

        # Show individual posts if verbose mode is enabled
        if verbose:
            print(f"\n{post_header}")
            print(f"URL: {post['url']}")
            if post.get("is_pinned"):
                print("(This is a pinned post)")

        # Only include selftext if it's not empty, to avoid feeding irrelevant empty strings to Gemini
        if post["selftext"].strip():
            all_posts_content += f"{post['selftext']}\n"
            if verbose:
                print(
                    f"Text: {post['selftext'][:200]}..."
                    if len(post["selftext"]) > 200
                    else f"Text: {post['selftext']}"
                )

        if post["comments"]:
            all_posts_content += "Top Comments:\n"
            if verbose:
                print(f"Comments ({len(post['comments'])}):")
            for comment_data in post["comments"]:
                # Handle both old string format (if cached) and new dict format
                if isinstance(comment_data, str):
                    body = comment_data
                    url = ""
                else:
                    body = comment_data["body"]
                    url = comment_data["url"]

                # Filter out "[deleted]" or "[removed]" comments
                if (
                    body.strip()
                    and not body.startswith("[deleted]")
                    and not body.startswith("[removed]")
                ):
                    all_posts_content += f"- {body}"
                    if url:
                        all_posts_content += f" (Source: {url})"
                    all_posts_content += "\n"

                    if verbose:
                        display_text = body[:100] + "..." if len(body) > 100 else body
                        print(f"  - {display_text}")
        all_posts_content += "\n"

    print("Generating summary with Gemini (this may take a moment)...")
    summary = summarizer.generate_summary(all_posts_content)

    if not summary:
        print(
            "Failed to generate summary. Please check your Gemini API key and network connection."
        )
        return

    formatted_output = output_formatter.format_summary(summary)
    print("\n" + formatted_output)

    # Save as HTML if requested
    if html_output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"wsb_summary_{timestamp}.html"
        html_path = os.path.join(os.getcwd(), html_filename)

        if html_formatter.save_html_report(summary, html_path, subreddit):
            print(f"\n✅ HTML report saved to: {html_path}")
        else:
            print("\n❌ Failed to save HTML report")


if __name__ == "__main__":
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
    main(
        num_posts=args.posts,
        subreddit=args.subreddit,
        verbose=args.verbose,
        sort_by=args.sort,
        skip_pinned=args.skip_pinned,
        html_output=args.html,
    )
