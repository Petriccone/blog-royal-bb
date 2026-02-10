"""
Camada de storage para artigos do blog de água.

Usa SQLite para persistir:
- artigos brutos extraídos das fontes externas
- estado de processamento (raw, processed, failed)

Este módulo é pensado para ser simples e determinístico, podendo ser
chamado por qualquer script em `execution/`.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "blog_agua.db"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_conn() -> Iterable[sqlite3.Connection]:
    """
    Context manager para conexão SQLite.
    Garante criação do diretório de dados e configurações básicas.
    """
    _ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """
    Cria as tabelas necessárias se ainda não existirem.
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                original_url TEXT NOT NULL UNIQUE,
                title TEXT,
                raw_text TEXT,
                language TEXT,
                scraped_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'raw', -- raw | processed | failed
                failure_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                output_path TEXT NOT NULL,
                image_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(article_id) REFERENCES articles(id)
            )
            """
        )


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


def upsert_raw_article(
    source: str,
    original_url: str,
    title: Optional[str],
    raw_text: str,
    language: Optional[str] = None,
) -> int:
    """
    Insere um novo artigo bruto ou atualiza um existente (re-scrape).
    Ao atualizar, define status='raw' e limpa failure_reason para o pipeline processar de novo.
    """
    init_db()
    now = _now_iso()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM articles WHERE original_url = ?",
            (original_url,),
        )
        row = cur.fetchone()
        if row:
            aid = int(row["id"])
            cur.execute(
                """
                UPDATE articles
                SET title = ?, raw_text = ?, language = ?, scraped_at = ?,
                    status = 'raw', failure_reason = NULL, updated_at = ?
                WHERE id = ?
                """,
                (title, raw_text, language, now, now, aid),
            )
            return aid
        cur.execute(
            """
            INSERT INTO articles (
                source, original_url, title, raw_text, language,
                scraped_at, status, failure_reason, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'raw', NULL, ?, ?)
            """,
            (source, original_url, title, raw_text, language, now, now, now),
        )
        return int(cur.lastrowid)


def fetch_unprocessed_articles(limit: Optional[int] = None) -> List[Article]:
    """
    Retorna artigos com status = 'raw', limitando a quantidade se informado.
    """
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        sql = "SELECT * FROM articles WHERE status = 'raw' ORDER BY scraped_at ASC"
        if limit is not None:
            sql += " LIMIT ?"
            cur.execute(sql, (limit,))
        else:
            cur.execute(sql)
        rows = cur.fetchall()
        return [Article(**dict(row)) for row in rows]


def fetch_articles_by_status(status: str, limit: Optional[int] = None) -> List[Article]:
    """
    Retorna artigos por status (raw, processed, failed), ordenados por scraped_at.
    """
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        sql = "SELECT * FROM articles WHERE status = ? ORDER BY scraped_at ASC"
        if limit is not None:
            sql += " LIMIT ?"
            cur.execute(sql, (status, limit))
        else:
            cur.execute(sql, (status,))
        rows = cur.fetchall()
        return [Article(**dict(row)) for row in rows]


def mark_article_processed(article_id: int) -> None:
    """
    Marca artigo como processado com sucesso.
    """
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE articles
            SET status = 'processed',
                failure_reason = NULL,
                updated_at = ?
            WHERE id = ?
            """,
            (_now_iso(), article_id),
        )


def mark_article_failed(article_id: int, reason: str) -> None:
    """
    Marca artigo como falho, armazenando motivo textual.
    """
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE articles
            SET status = 'failed',
                failure_reason = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (reason[:4000], _now_iso(), article_id),
        )


def register_post(
    article_id: int,
    slug: str,
    output_path: str,
    image_path: Optional[str] = None,
) -> int:
    """
    Registra um post gerado para um artigo.
    """
    init_db()
    now = _now_iso()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO posts (
                article_id, slug, output_path, image_path,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (article_id, slug, output_path, image_path, now, now),
        )
        return int(cur.lastrowid)


def get_article_by_id(article_id: int) -> Optional[Article]:
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        row = cur.fetchone()
        if not row:
            return None
        return Article(**dict(row))


def list_posts() -> List[Dict[str, Any]]:
    """
    Lista posts registrados com alguns metadados básicos.
    """
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

