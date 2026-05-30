from . import config
from . import reddit
from . import storage


def scrape_posts(
    num_posts: int | None = None,
    subreddit: str | None = None,
    sort_by: str = "hot",
    skip_pinned: bool = False,
) -> list[dict] | None:
    num_posts = num_posts or config.NUM_POSTS_TO_FETCH
    subreddit = subreddit or config.SUBREDDIT_NAME

    if not config.REDDIT_CLIENT_ID or not config.REDDIT_CLIENT_SECRET:
        print("Error: Please set your Reddit API keys in .env before scraping.")
        return None

    sort_label = sort_by if sort_by != "hot" else "hot (trending)"
    skip_label = " (skipping pinned)" if skip_pinned else ""
    print(f"Fetching {num_posts} {sort_label} posts from r/{subreddit}{skip_label}...")

    posts = reddit.fetch_top_posts(
        num_posts=num_posts,
        subreddit=subreddit,
        sort_by=sort_by,
        skip_pinned=skip_pinned,
        fetch_comments=False,
    )

    if not posts:
        print(
            "Failed to fetch Reddit posts. Please check your network connection or API credentials."
        )
        return None

    post_ids = [post["reddit_id"] for post in posts if post.get("reddit_id")]
    existing_ids = storage.existing_post_ids(post_ids)
    new_ids = set(post_ids) - existing_ids
    stale_ids = storage.posts_needing_comment_refresh(
        list(existing_ids), config.COMMENT_REFRESH_HOURS
    )
    comment_refresh_ids = new_ids | stale_ids

    if comment_refresh_ids:
        print(
            f"Refreshing comments for {len(comment_refresh_ids)} new or stale posts..."
        )
        comments_by_post = reddit.fetch_comments_for_posts(
            sorted(comment_refresh_ids)
        )
        for post in posts:
            post["comments"] = comments_by_post.get(post.get("reddit_id"), [])
    else:
        print("All stored comments are fresh. Skipping comment refresh.")

    print(f"Successfully fetched {len(posts)} posts. Saving scrape data to SQLite...")
    return storage.save_posts(posts, subreddit)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Reddit data into SQLite")
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
    args = parser.parse_args()

    posts = scrape_posts(
        num_posts=args.posts,
        subreddit=args.subreddit,
        sort_by=args.sort,
        skip_pinned=args.skip_pinned,
    )
    if posts:
        print("Scrape complete.")


if __name__ == "__main__":
    main()
