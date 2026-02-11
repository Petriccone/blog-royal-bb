"""
Backend PostgreSQL para o storage (Supabase ou qualquer Postgres).

Ativo quando DATABASE_URL está definida. Usa a mesma API que storage_sqlite.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"


@dataclass
class Article:
    id: int
    source: str
    original_url: str
    title: Optional[str]
    raw_text: str
    language: Optional[str]
    scraped_at: str
    status: str
    failure_reason: Optional[str]
    created_at: str
    updated_at: str


@contextmanager
def get_conn() -> Iterable[psycopg2.extensions.connection]:
    """
    Context manager para conexão PostgreSQL (DATABASE_URL).
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL não definida. Para usar Postgres/Supabase, defina DATABASE_URL.")
    conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """
    Cria as tabelas necessárias se ainda não existirem (PostgreSQL).
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                original_url TEXT NOT NULL UNIQUE,
                title TEXT,
                raw_text TEXT,
                language TEXT,
                scraped_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'raw',
                failure_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                article_id INTEGER NOT NULL REFERENCES articles(id),
                slug TEXT NOT NULL UNIQUE,
                output_path TEXT NOT NULL,
                image_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def upsert_raw_article(
    source: str,
    original_url: str,
    title: Optional[str],
    raw_text: str,
    language: Optional[str] = None,
) -> int:
    init_db()
    now = _now_iso()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, status FROM articles WHERE original_url = %s",
            (original_url,),
        )
        row = cur.fetchone()
        if row:
            aid = int(row["id"])
            current_status = (row["status"] or "").strip().lower()
            if current_status == "processed":
                cur.execute(
                    """
                    UPDATE articles
                    SET title = %s, raw_text = %s, language = %s, scraped_at = %s, updated_at = %s
                    WHERE id = %s
                    """,
                    (title, raw_text, language, now, now, aid),
                )
            else:
                cur.execute(
                    """
                    UPDATE articles
                    SET title = %s, raw_text = %s, language = %s, scraped_at = %s,
                        status = 'raw', failure_reason = NULL, updated_at = %s
                    WHERE id = %s
                    """,
                    (title, raw_text, language, now, now, aid),
                )
            return aid
        cur.execute(
            """
            INSERT INTO articles (
                source, original_url, title, raw_text, language,
                scraped_at, status, failure_reason, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, 'raw', NULL, %s, %s)
            RETURNING id
            """,
            (source, original_url, title, raw_text, language, now, now, now),
        )
        return int(cur.fetchone()["id"])


def fetch_unprocessed_articles(limit: Optional[int] = None) -> List[Article]:
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        sql = "SELECT * FROM articles WHERE status = 'raw' ORDER BY scraped_at ASC"
        if limit is not None:
            sql += " LIMIT %s"
            cur.execute(sql, (limit,))
        else:
            cur.execute(sql)
        rows = cur.fetchall()
        return [_row_to_article(row) for row in rows]


def fetch_articles_by_status(status: str, limit: Optional[int] = None) -> List[Article]:
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        sql = "SELECT * FROM articles WHERE status = %s ORDER BY scraped_at ASC"
        if limit is not None:
            sql += " LIMIT %s"
            cur.execute(sql, (status, limit))
        else:
            cur.execute(sql, (status,))
        rows = cur.fetchall()
        return [_row_to_article(row) for row in rows]


def _row_to_article(row: Dict[str, Any]) -> Article:
    return Article(
        id=int(row["id"]),
        source=str(row["source"]),
        original_url=str(row["original_url"]),
        title=row["title"],
        raw_text=row["raw_text"] or "",
        language=row["language"],
        scraped_at=str(row["scraped_at"]),
        status=str(row["status"]),
        failure_reason=row["failure_reason"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def mark_article_processed(article_id: int) -> None:
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE articles
            SET status = 'processed', failure_reason = NULL, updated_at = %s
            WHERE id = %s
            """,
            (_now_iso(), article_id),
        )


def mark_article_failed(article_id: int, reason: str) -> None:
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE articles
            SET status = 'failed', failure_reason = %s, updated_at = %s
            WHERE id = %s
            """,
            (reason[:4000], _now_iso(), article_id),
        )


def register_post(
    article_id: int,
    slug: str,
    output_path: str,
    image_path: Optional[str] = None,
) -> int:
    init_db()
    now = _now_iso()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO posts (
                article_id, slug, output_path, image_path,
                created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (article_id, slug, output_path, image_path, now, now),
        )
        return int(cur.fetchone()["id"])


def get_article_by_id(article_id: int) -> Optional[Article]:
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM articles WHERE id = %s", (article_id,))
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_article(row)


def get_post_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, article_id, slug, output_path FROM posts WHERE slug = %s",
            (slug,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)


def list_posts() -> List[Dict[str, Any]]:
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.slug, p.output_path, p.image_path,
                   a.source, a.original_url, a.title
            FROM posts p
            JOIN articles a ON a.id = p.article_id
            ORDER BY p.created_at DESC
            """
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]
