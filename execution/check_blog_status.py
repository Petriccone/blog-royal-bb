"""
Mostra rapidamente: quantos posts existem no disco, quantos artigos no banco por status.
Uso: python -m execution.check_blog_status
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = PROJECT_ROOT / "web" / "content" / "posts"
IMAGES_DIR = PROJECT_ROOT / "web" / "public" / "images" / "posts"


def main() -> None:
    posts = list(POSTS_DIR.glob("*.md")) if POSTS_DIR.exists() else []
    images = list(IMAGES_DIR.glob("*")) if IMAGES_DIR.exists() else []

    print("--- Blog Royal B&B — status ---")
    print(f"Posts em disco (web/content/posts): {len(posts)}")
    print(f"Imagens (web/public/images/posts): {len(images)}")

    try:
        from execution.utils import storage

        storage.init_db()
        with storage.get_conn() as conn:
            cur = conn.cursor()
            for status in ("raw", "processed", "failed"):
                cur.execute("SELECT COUNT(*) FROM articles WHERE status = ?", (status,))
                n = cur.fetchone()[0]
                print(f"Artigos no banco (status={status}): {n}")
    except Exception as e:
        print(f"Banco (data/blog_agua.db): {e}")

    print("-------------------------------")
    print("Para subir os posts para o site: python -m execution.push_content_to_github")
    print("Ver DEPLOY.md para Vercel (Root Directory = web) e push para GitHub.")


if __name__ == "__main__":
    main()
