import os
from datetime import datetime

import pytz

from . import config
from . import editor
from . import html
from . import llm
from . import news
from . import storage
from . import writer


def generate_report(
    posts: list[dict] | None = None,
    num_posts: int | None = None,
    subreddit: str | None = None,
    verbose: bool = False,
    html_output: bool = False,
    output_file: str | None = None,
    markdown_output_file: str | None = None,
    dry_run: bool = False,
    edit_pass: bool | None = None,
    with_news: bool | None = None,
) -> str | None:
    num_posts = num_posts or config.NUM_POSTS_TO_FETCH
    subreddit = subreddit or config.SUBREDDIT_NAME

    if posts is None:
        posts = storage.load_recent_posts(subreddit, num_posts)

    if not posts:
        print("No stored posts found. Run a scrape before generating a report.")
        return None

    posts = storage.add_report_deltas(posts, subreddit)

    print("Aggregating stored content for summarization...")
    all_posts_content = build_posts_content(posts, subreddit=subreddit, verbose=verbose)
    news_items = []

    if with_news is None:
        with_news = config.REPORT_WITH_NEWS
    if with_news:
        print("Extracting news topics from posts via LLM...")
        queries = _extract_news_queries(posts)
        if queries:
            print(f"News search queries: {queries}")
            print("Fetching external news context...")
            news_context, news_items = news.build_news_context_from_queries(queries)
            if news_context:
                all_posts_content += "\n" + news_context
            else:
                print("No external news context found.")
        else:
            print("No news topics extracted from posts.")

    if dry_run:
        print("\n" + all_posts_content)
        return all_posts_content

    try:
        llm.validate_config()
    except llm.LLMConfigError as e:
        print(f"Error: {e}")
        return None

    print(
        f"Generating summary with {config.get_llm_display_name()} "
        "(this may take a moment)..."
    )
    summary = writer.generate_summary(all_posts_content)

    if not summary:
        print(
            "Failed to generate summary. Please check your LLM API key and network connection."
        )
        return None

    if edit_pass is None:
        edit_pass = config.REPORT_EDIT_PASS
    if edit_pass:
        print(
            f"Editing summary with {config.get_llm_display_name()} "
            "(second pass for source grounding and polish)..."
        )
        edited_summary = editor.edit_summary(all_posts_content, summary)
        if edited_summary:
            summary = edited_summary
        else:
            print("Editor pass failed. Continuing with the unedited draft.")

    markdown = summary
    report_date = datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d")
    report_id = storage.save_report(markdown, report_date, subreddit)
    storage.save_report_news_items(report_id, news_items)
    print("\n" + markdown)

    _save_markdown_file(markdown, markdown_output_file)
    _save_html_file(summary, subreddit, html_output, output_file)
    return markdown


def build_posts_content(
    posts: list[dict], subreddit: str | None = None, verbose: bool = False
) -> str:
    all_posts_content = ""
    for i, post in enumerate(posts):
        pinned_marker = "[PINNED] " if post.get("is_pinned", False) else ""
        post_header = f"--- Post {i + 1}: {pinned_marker}{post['title']} ---"
        all_posts_content += post_header + "\n"
        all_posts_content += _format_post_metadata(post, subreddit=subreddit)

        if verbose:
            print(f"\n{post_header}")
            print(f"URL: {post['url']}")
            print(_format_metrics_for_log(post))
            if post.get("is_pinned"):
                print("(This is a pinned post)")

        selftext = post.get("selftext") or ""
        if selftext.strip():
            all_posts_content += f"Post Body: {_clip_text(selftext)}\n"
            if verbose:
                print(
                    f"Text: {selftext[:200]}..."
                    if len(selftext) > 200
                    else f"Text: {selftext}"
                )

        comments = _reportable_comments(post.get("comments", []))
        if comments:
            all_posts_content += "Top Comments:\n"
            if verbose:
                print(
                    f"Comments included ({len(comments)} of "
                    f"{len(post.get('comments', []))})"
                )
            for comment_data in comments:
                body = _clip_text(comment_data["body"])
                all_posts_content += "- "
                score = comment_data.get("score")
                if score is not None:
                    all_posts_content += f"[score {score}] "
                if comment_data.get("author"):
                    all_posts_content += f"u/{comment_data['author']}: "
                all_posts_content += body
                if comment_data.get("url"):
                    all_posts_content += f" (Source: {comment_data['url']})"
                all_posts_content += "\n"

                if verbose:
                    display_text = body[:100] + "..." if len(body) > 100 else body
                    print(f"  - {display_text}")
        all_posts_content += "\n"

    return all_posts_content


def _format_post_metadata(post: dict, subreddit: str | None = None) -> str:
    discussion_url = _post_discussion_url(post, subreddit)
    lines = [
        f"Post Discussion URL: {discussion_url}",
    ]
    if post.get("url") and post["url"] != discussion_url:
        lines.append(f"Post External URL: {post['url']}")
    if post.get("author"):
        lines.append(f"Author: u/{post['author']}")
    if post.get("score") is not None:
        lines.append(f"Score: {post['score']}")
    if post.get("upvote_ratio") is not None:
        lines.append(f"Upvote Ratio: {post['upvote_ratio']}")
    if post.get("num_comments") is not None:
        lines.append(f"Reddit Comment Count: {post['num_comments']}")
    if post.get("previous_report_at"):
        lines.append(
            "New Since Previous Report: "
            f"{'yes' if post.get('new_since_previous_report') else 'no'}"
        )
        _append_delta(
            lines,
            "Score Change Since Previous Report",
            post.get("score_change_since_previous_report"),
        )
        _append_delta(
            lines,
            "Comment Count Change Since Previous Report",
            post.get("comment_count_change_since_previous_report"),
        )
        _append_delta(
            lines,
            "Upvote Ratio Change Since Previous Report",
            post.get("upvote_ratio_change_since_previous_report"),
        )
    return "\n".join(lines) + "\n"


def _post_discussion_url(post: dict, subreddit: str | None = None) -> str:
    reddit_id = post.get("reddit_id")
    if reddit_id:
        subreddit = subreddit or post.get("subreddit") or config.SUBREDDIT_NAME
        return f"https://www.reddit.com/r/{subreddit}/comments/{reddit_id}/"
    return post.get("url", "")


def _append_delta(lines: list[str], label: str, value: int | float | None) -> None:
    if value is None:
        return
    if isinstance(value, float):
        value = round(value, 4)
    sign = "+" if value > 0 else ""
    lines.append(f"{label}: {sign}{value}")


def _format_metrics_for_log(post: dict) -> str:
    metrics = []
    for label, key in (
        ("score", "score"),
        ("upvote_ratio", "upvote_ratio"),
        ("comments", "num_comments"),
    ):
        if post.get(key) is not None:
            metrics.append(f"{label}: {post[key]}")
    return ", ".join(metrics)


def _reportable_comments(comments: list[dict | str]) -> list[dict]:
    reportable = []
    for comment in comments:
        if isinstance(comment, str):
            comment = {"body": comment}

        body = (comment.get("body") or "").strip()
        if not body:
            continue
        if body.startswith("[deleted]") or body.startswith("[removed]"):
            continue

        reportable.append(comment)

    return sorted(
        reportable,
        key=lambda item: item.get("score") if item.get("score") is not None else -1,
        reverse=True,
    )[: config.REPORT_COMMENTS_PER_POST]


def _clip_text(text: str) -> str:
    words = text.strip().split()
    max_words = config.REPORT_MAX_BODY_WORDS
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip() + "..."


def _extract_news_queries(posts: list[dict]) -> list[str]:
    titles = []
    for post in posts:
        score = post.get("score", 0)
        title = post.get("title", "")
        titles.append(f"[score {score}] {title}")

    prompt = (
        "Extract 3-8 specific stock, market, or financial news search queries "
        "relevant to these Reddit posts. Return ONLY the queries, one per line, "
        "no numbering, no bullets, no extra text. Each query 2-5 words.\n\n"
        "Examples:\n"
        "Nvidia stock news\n"
        "Federal Reserve interest rates\n"
        "crude oil prices\n\n"
        "Posts:\n"
        + "\n".join(titles)
    )

    response = llm.generate([llm.LLMMessage(role="user", content=prompt)])
    if not response or not response.text:
        return []

    queries = []
    for line in response.text.strip().split("\n"):
        line = line.strip().strip('"').strip("*").strip("-").strip()
        if line and not line.startswith(("Here", "Based", "Post", "Example", "Extract")):
            queries.append(line)
    return queries[: config.NEWS_MAX_TERMS]


def _save_markdown_file(markdown: str, markdown_output_file: str | None) -> None:
    if not markdown_output_file:
        return

    try:
        if os.path.isabs(markdown_output_file):
            md_path = markdown_output_file
        else:
            md_path = os.path.join(os.getcwd(), markdown_output_file)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"\n✅ Markdown report saved to: {md_path}")
    except Exception as e:
        print(f"\n❌ Failed to save Markdown report: {e}")


def _save_html_file(
    summary: str,
    subreddit: str,
    html_output: bool,
    output_file: str | None,
) -> None:
    if not html_output and not output_file:
        return

    if output_file:
        html_filename = output_file
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"wsb_summary_{timestamp}.html"

    if os.path.isabs(html_filename):
        html_path = html_filename
    else:
        html_path = os.path.join(os.getcwd(), html_filename)

    if html.save_html_report(summary, html_path, subreddit):
        print(f"\n✅ HTML report saved to: {html_path}")
    else:
        print("\n❌ Failed to save HTML report")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate a report from SQLite")
    parser.add_argument(
        "-p",
        "--posts",
        type=int,
        default=config.NUM_POSTS_TO_FETCH,
        help=f"Number of stored posts to include (default: {config.NUM_POSTS_TO_FETCH})",
    )
    parser.add_argument(
        "-s",
        "--subreddit",
        type=str,
        default=config.SUBREDDIT_NAME,
        help=f"Subreddit to report on (default: {config.SUBREDDIT_NAME})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show individual posts for debugging",
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
        help="Print the LLM input without calling the LLM",
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

    generate_report(
        num_posts=args.posts,
        subreddit=args.subreddit,
        verbose=args.verbose,
        html_output=args.html,
        output_file=args.output,
        markdown_output_file=args.markdown_output,
        dry_run=args.dry_run,
        edit_pass=args.edit_pass,
        with_news=args.with_news,
    )


if __name__ == "__main__":
    main()
