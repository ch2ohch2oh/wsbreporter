import praw
from . import config


def fetch_top_posts(num_posts=None, subreddit=None, sort_by="hot", skip_pinned=False):
    """
    Fetches posts from the configured subreddit.

    Args:
        num_posts: Number of posts to fetch (default: from config)
        subreddit: Subreddit name to fetch from (default: from config)
        sort_by: How to sort posts - 'hot', 'new', 'top', 'rising' (default: 'hot')
        skip_pinned: Skip pinned/stickied posts like weekly threads (default: False)

    Returns:
        list: A list of dictionaries, where each dictionary represents a post
              with its title, body, and top comments.
        None: If an error occurs during fetching.
    """
    # Use provided arguments or fall back to config defaults
    num_posts = num_posts or config.NUM_POSTS_TO_FETCH
    subreddit = subreddit or config.SUBREDDIT_NAME
    try:
        reddit = praw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.REDDIT_USER_AGENT,
        )

        subreddit_obj = reddit.subreddit(subreddit)
        posts_data = []

        # Choose the sorting method
        # Fetch more than needed to account for skipped pinned posts
        fetch_limit = num_posts * 3 if skip_pinned else num_posts

        if sort_by == "hot":
            submissions = subreddit_obj.hot(limit=fetch_limit)
        elif sort_by == "new":
            submissions = subreddit_obj.new(limit=fetch_limit)
        elif sort_by == "rising":
            submissions = subreddit_obj.rising(limit=fetch_limit)
        else:  # top
            submissions = subreddit_obj.top(limit=fetch_limit)

        for submission in submissions:
            # Skip pinned/stickied posts if requested
            if skip_pinned and submission.stickied:
                continue

            # Stop if we've collected enough posts
            if len(posts_data) >= num_posts:
                break

            post_comments = []
            # Fetch top comments, up to a certain limit or depth
            submission.comments.replace_more(limit=0)  # Flatten comments
            for i, comment in enumerate(submission.comments):
                if i >= config.NUM_COMMENTS_TO_FETCH:  # Limit comments based on config
                    break
                if hasattr(comment, "body"):
                    comment_link = f"https://www.reddit.com{comment.permalink}"
                    post_comments.append(
                        {
                            "body": comment.body,
                            "url": comment_link,
                            "score": comment.score,
                        }
                    )

            posts_data.append(
                {
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "url": submission.url,
                    "score": submission.score,
                    "comments": post_comments,
                    "is_pinned": submission.stickied,  # Mark if it's a pinned post
                }
            )
        return posts_data
    except Exception as e:
        print(f"Error fetching Reddit posts: {e}")
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch posts from a subreddit using the Reddit API"
    )
    parser.add_argument(
        "-s",
        "--subreddit",
        type=str,
        default=config.SUBREDDIT_NAME,
        help=f"Subreddit to fetch from (default: {config.SUBREDDIT_NAME})",
    )
    parser.add_argument(
        "-n",
        "--num-posts",
        type=int,
        default=config.NUM_POSTS_TO_FETCH,
        help=f"Number of posts to fetch (default: {config.NUM_POSTS_TO_FETCH})",
    )
    parser.add_argument(
        "--sort",
        type=str,
        choices=["hot", "new", "top", "rising"],
        default="hot",
        help="How to sort posts (default: hot)",
    )
    parser.add_argument(
        "--skip-pinned",
        action="store_true",
        help="Skip pinned/stickied posts like weekly threads",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed output including comments",
    )

    args = parser.parse_args()

    print(
        f"Fetching {args.num_posts} {args.sort} posts from r/{args.subreddit}"
        + (" (skipping pinned)" if args.skip_pinned else "")
        + "..."
    )

    posts = fetch_top_posts(
        num_posts=args.num_posts,
        subreddit=args.subreddit,
        sort_by=args.sort,
        skip_pinned=args.skip_pinned,
    )

    if posts:
        for i, post in enumerate(posts):
            print(f"\n--- Post {i + 1} ---")
            print(f"Title: {post['title']}")
            print(f"Score: {post['score']} upvotes")
            print(f"URL: {post['url']}")
            if post["selftext"]:
                print(f"Selftext: {post['selftext'][:200]}...")  # Print first 200 chars
            if args.verbose and post["comments"]:
                print(f"Comments ({len(post['comments'])}):")
                for j, comment in enumerate(post["comments"][:5], 1):  # Show first 5
                    print(
                        f"  {j}. [{comment['score']} upvotes] {comment['body'][:100]}..."
                    )
    else:
        print("Failed to fetch posts.")
