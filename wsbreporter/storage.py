import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from . import config


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS posts (
                reddit_id TEXT PRIMARY KEY,
                subreddit TEXT NOT NULL,
                title TEXT NOT NULL,
                selftext TEXT,
                url TEXT NOT NULL,
                author TEXT,
                created_utc TEXT,
                first_scraped_at TEXT NOT NULL,
                last_scraped_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comments (
                reddit_id TEXT PRIMARY KEY,
                post_reddit_id TEXT NOT NULL,
                body TEXT NOT NULL,
                author TEXT,
                url TEXT,
                created_utc TEXT,
                first_scraped_at TEXT NOT NULL,
                last_scraped_at TEXT NOT NULL,

                FOREIGN KEY (post_reddit_id) REFERENCES posts(reddit_id)
            );

            CREATE TABLE IF NOT EXISTS post_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_reddit_id TEXT NOT NULL,
                scraped_at TEXT NOT NULL,
                score INTEGER,
                upvote_ratio REAL,
                num_comments INTEGER,
                is_pinned INTEGER NOT NULL DEFAULT 0,

                FOREIGN KEY (post_reddit_id) REFERENCES posts(reddit_id)
            );

            CREATE TABLE IF NOT EXISTS comment_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_reddit_id TEXT NOT NULL,
                scraped_at TEXT NOT NULL,
                score INTEGER,

                FOREIGN KEY (comment_reddit_id) REFERENCES comments(reddit_id)
            );

            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL,
                subreddit TEXT NOT NULL,
                llm_provider TEXT NOT NULL,
                llm_model TEXT NOT NULL,
                markdown TEXT NOT NULL,
                generated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS news_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                query TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                source_name TEXT,
                published_at TEXT,
                summary TEXT,
                fetched_at TEXT NOT NULL,
                raw TEXT,

                UNIQUE(provider, query, url)
            );

            CREATE TABLE IF NOT EXISTS report_news_items (
                report_id INTEGER NOT NULL,
                news_item_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                included_at TEXT NOT NULL,

                PRIMARY KEY (report_id, news_item_id, query),
                FOREIGN KEY (report_id) REFERENCES reports(id),
                FOREIGN KEY (news_item_id) REFERENCES news_items(id)
            );

            CREATE INDEX IF NOT EXISTS idx_posts_subreddit_last_scraped
            ON posts(subreddit, last_scraped_at);

            CREATE INDEX IF NOT EXISTS idx_comments_post
            ON comments(post_reddit_id);

            CREATE INDEX IF NOT EXISTS idx_post_snapshots_post_time
            ON post_snapshots(post_reddit_id, scraped_at);

            CREATE INDEX IF NOT EXISTS idx_comment_snapshots_comment_time
            ON comment_snapshots(comment_reddit_id, scraped_at);

            CREATE INDEX IF NOT EXISTS idx_reports_date_subreddit
            ON reports(report_date, subreddit);

            CREATE INDEX IF NOT EXISTS idx_news_items_query_fetched
            ON news_items(provider, query, fetched_at);

            CREATE INDEX IF NOT EXISTS idx_report_news_items_report
            ON report_news_items(report_id);
            """
        )


def save_posts(posts: list[dict[str, Any]], subreddit: str) -> list[dict[str, Any]]:
    scraped_at = _now_utc()
    init_db()

    with _connect() as conn:
        for post in posts:
            post_id = post.get("reddit_id")
            if not post_id:
                continue

            conn.execute(
                """
                INSERT INTO posts (
                    reddit_id, subreddit, title, selftext, url, author, created_utc,
                    first_scraped_at, last_scraped_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(reddit_id) DO UPDATE SET
                    subreddit = excluded.subreddit,
                    title = excluded.title,
                    selftext = excluded.selftext,
                    url = excluded.url,
                    author = excluded.author,
                    created_utc = excluded.created_utc,
                    last_scraped_at = excluded.last_scraped_at
                """,
                (
                    post_id,
                    subreddit,
                    post.get("title", ""),
                    post.get("selftext", ""),
                    post.get("url", ""),
                    post.get("author"),
                    post.get("created_utc"),
                    scraped_at,
                    scraped_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO post_snapshots (
                    post_reddit_id, scraped_at, score, upvote_ratio, num_comments,
                    is_pinned
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    post_id,
                    scraped_at,
                    post.get("score"),
                    post.get("upvote_ratio"),
                    post.get("num_comments"),
                    int(bool(post.get("is_pinned", False))),
                ),
            )

            for comment in post.get("comments", []):
                if isinstance(comment, str):
                    continue

                comment_id = comment.get("reddit_id")
                if not comment_id:
                    continue

                conn.execute(
                    """
                    INSERT INTO comments (
                        reddit_id, post_reddit_id, body, author, url, created_utc,
                        first_scraped_at, last_scraped_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(reddit_id) DO UPDATE SET
                        post_reddit_id = excluded.post_reddit_id,
                        body = excluded.body,
                        author = excluded.author,
                        url = excluded.url,
                        created_utc = excluded.created_utc,
                        last_scraped_at = excluded.last_scraped_at
                    """,
                    (
                        comment_id,
                        post_id,
                        comment.get("body", ""),
                        comment.get("author"),
                        comment.get("url"),
                        comment.get("created_utc"),
                        scraped_at,
                        scraped_at,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO comment_snapshots (
                        comment_reddit_id, scraped_at, score
                    )
                    VALUES (?, ?, ?)
                    """,
                    (comment_id, scraped_at, comment.get("score")),
                )

    return load_posts([post["reddit_id"] for post in posts if post.get("reddit_id")])


def load_posts(reddit_ids: list[str]) -> list[dict[str, Any]]:
    if not reddit_ids:
        return []

    init_db()
    placeholders = ",".join("?" for _ in reddit_ids)
    with _connect() as conn:
        post_rows = conn.execute(
            f"""
            SELECT
                p.reddit_id, p.title, p.selftext, p.url, p.author, p.created_utc,
                p.first_scraped_at, p.last_scraped_at,
                ps.score, ps.upvote_ratio, ps.num_comments, ps.is_pinned
            FROM posts p
            LEFT JOIN post_snapshots ps ON ps.id = (
                SELECT id
                FROM post_snapshots
                WHERE post_reddit_id = p.reddit_id
                ORDER BY scraped_at DESC, id DESC
                LIMIT 1
            )
            WHERE p.reddit_id IN ({placeholders})
            """,
            reddit_ids,
        ).fetchall()
        posts_by_id = {row["reddit_id"]: dict(row) for row in post_rows}

        comment_rows = conn.execute(
            f"""
            SELECT
                c.reddit_id, c.post_reddit_id, c.body, c.author, c.url,
                c.created_utc, cs.score
            FROM comments c
            LEFT JOIN comment_snapshots cs ON cs.id = (
                SELECT id
                FROM comment_snapshots
                WHERE comment_reddit_id = c.reddit_id
                ORDER BY scraped_at DESC, id DESC
                LIMIT 1
            )
            WHERE c.post_reddit_id IN ({placeholders})
            ORDER BY c.post_reddit_id, cs.score DESC
            """,
            reddit_ids,
        ).fetchall()

    for post in posts_by_id.values():
        post["comments"] = []
        post["is_pinned"] = bool(post.get("is_pinned"))

    for row in comment_rows:
        post = posts_by_id.get(row["post_reddit_id"])
        if post is not None:
            post["comments"].append(dict(row))

    return [posts_by_id[reddit_id] for reddit_id in reddit_ids if reddit_id in posts_by_id]


def load_recent_posts(subreddit: str, limit: int) -> list[dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT reddit_id
            FROM posts
            WHERE subreddit = ?
            ORDER BY last_scraped_at DESC
            LIMIT ?
            """,
            (subreddit, limit),
        ).fetchall()

    return load_posts([row["reddit_id"] for row in rows])


def add_report_deltas(
    posts: list[dict[str, Any]], subreddit: str
) -> list[dict[str, Any]]:
    previous_report_at = latest_report_generated_at(subreddit)
    for post in posts:
        post["previous_report_at"] = previous_report_at

    if not posts or not previous_report_at:
        return posts

    reddit_ids = [post["reddit_id"] for post in posts if post.get("reddit_id")]
    if not reddit_ids:
        return posts

    placeholders = ",".join("?" for _ in reddit_ids)
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT
                ps.post_reddit_id, ps.score, ps.upvote_ratio, ps.num_comments
            FROM post_snapshots ps
            WHERE ps.post_reddit_id IN ({placeholders})
              AND ps.id = (
                  SELECT id
                  FROM post_snapshots
                  WHERE post_reddit_id = ps.post_reddit_id
                    AND scraped_at <= ?
                  ORDER BY scraped_at DESC, id DESC
                  LIMIT 1
              )
            """,
            [*reddit_ids, previous_report_at],
        ).fetchall()

    previous_by_id = {row["post_reddit_id"]: dict(row) for row in rows}
    for post in posts:
        previous = previous_by_id.get(post.get("reddit_id"))
        post["new_since_previous_report"] = previous is None
        if previous is None:
            continue

        post["score_change_since_previous_report"] = _number_delta(
            post.get("score"), previous.get("score")
        )
        post["comment_count_change_since_previous_report"] = _number_delta(
            post.get("num_comments"), previous.get("num_comments")
        )
        post["upvote_ratio_change_since_previous_report"] = _number_delta(
            post.get("upvote_ratio"), previous.get("upvote_ratio")
        )

    return posts


def latest_report_generated_at(subreddit: str) -> str | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT generated_at
            FROM reports
            WHERE subreddit = ?
            ORDER BY generated_at DESC, id DESC
            LIMIT 1
            """,
            (subreddit,),
        ).fetchone()

    return row["generated_at"] if row else None


def existing_post_ids(reddit_ids: list[str]) -> set[str]:
    if not reddit_ids:
        return set()

    init_db()
    placeholders = ",".join("?" for _ in reddit_ids)
    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT reddit_id
            FROM posts
            WHERE reddit_id IN ({placeholders})
            """,
            reddit_ids,
        ).fetchall()

    return {row["reddit_id"] for row in rows}


def posts_needing_comment_refresh(
    reddit_ids: list[str], refresh_hours: int
) -> set[str]:
    if not reddit_ids:
        return set()

    cutoff = (
        datetime.now(timezone.utc) - timedelta(hours=refresh_hours)
    ).isoformat(timespec="seconds")
    placeholders = ",".join("?" for _ in reddit_ids)
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT p.reddit_id
            FROM posts p
            LEFT JOIN (
                SELECT post_reddit_id, MAX(last_scraped_at) AS comments_scraped_at
                FROM comments
                GROUP BY post_reddit_id
            ) c ON c.post_reddit_id = p.reddit_id
            WHERE p.reddit_id IN ({placeholders})
              AND (
                  c.comments_scraped_at IS NULL
                  OR c.comments_scraped_at < ?
              )
            """,
            [*reddit_ids, cutoff],
        ).fetchall()

    return {row["reddit_id"] for row in rows}


def save_report(markdown: str, report_date: str, subreddit: str) -> int:
    init_db()
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO reports (
                report_date, subreddit, llm_provider, llm_model, markdown,
                generated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                report_date,
                subreddit,
                config.LLM_PROVIDER,
                config.get_llm_model_name() or "",
                markdown,
                _now_utc(),
            ),
        )
        return int(cursor.lastrowid)


def save_report_news_items(report_id: int, items: list[dict[str, Any]]) -> None:
    if not report_id or not items:
        return

    init_db()
    included_at = _now_utc()
    with _connect() as conn:
        for item in items:
            item_id = item.get("id")
            if not item_id:
                continue
            conn.execute(
                """
                INSERT OR IGNORE INTO report_news_items (
                    report_id, news_item_id, query, included_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (report_id, item_id, item.get("query", ""), included_at),
            )


def _connect() -> sqlite3.Connection:
    db_path = _database_path()
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _database_path() -> str:
    if os.path.isabs(config.DATABASE_PATH):
        return config.DATABASE_PATH

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, config.DATABASE_PATH)


def _number_delta(current: Any, previous: Any) -> int | float | None:
    if current is None or previous is None:
        return None
    return current - previous


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
