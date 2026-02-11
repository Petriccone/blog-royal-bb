"""
Camada de storage para artigos do blog de água.

- Se DATABASE_URL estiver definida (ex.: Supabase Postgres): usa PostgreSQL.
- Caso contrário: usa SQLite em data/blog_agua.db (local ou sem volume).

O mesmo código (pipeline, scrape) usa este módulo; a troca é transparente.
"""

from __future__ import annotations

import os

# Escolha do backend: Postgres (Supabase) ou SQLite
if os.getenv("DATABASE_URL", "").strip():
    from execution.utils import storage_pg as _backend
else:
    from execution.utils import storage_sqlite as _backend

Article = _backend.Article
get_conn = _backend.get_conn
init_db = _backend.init_db
upsert_raw_article = _backend.upsert_raw_article
fetch_unprocessed_articles = _backend.fetch_unprocessed_articles
fetch_articles_by_status = _backend.fetch_articles_by_status
mark_article_processed = _backend.mark_article_processed
mark_article_failed = _backend.mark_article_failed
register_post = _backend.register_post
get_article_by_id = _backend.get_article_by_id
get_post_by_slug = _backend.get_post_by_slug
list_posts = _backend.list_posts
