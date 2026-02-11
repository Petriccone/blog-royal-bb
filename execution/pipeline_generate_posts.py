"""
Pipeline que transforma artigos brutos em posts Markdown + imagens.

Fluxo:
- Busca artigos com status 'raw' no storage
- Para cada artigo, chama o mediator_agent (writer + reviewer)
- Se aprovado, chama image_agent e gera:
  - arquivo Markdown em web/content/posts/<slug>.md
  - download da imagem em web/public/images/posts/<slug>.png (quando possível)
- Atualiza o storage marcando o artigo como processado e registrando o post.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Limite de tamanho do slug para evitar "File name too long" (Errno 36)
MAX_SLUG_LENGTH = 80

import requests

from execution.agents import (
    image_agent,
    mediator_agent,
    image_prompt_designer_agent,
)
from execution.utils import storage


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = PROJECT_ROOT / "web"
POSTS_DIR = WEB_DIR / "content" / "posts"
IMAGES_DIR = WEB_DIR / "public" / "images" / "posts"

# Imagens fotográficas de fallback (URLs públicas) para quando
# a geração automática via Fal não estiver disponível.
FALLBACK_COVER_IMAGES = [
    "https://images.unsplash.com/photo-1582719478250-ccce7cd0a9b6?auto=format&fit=crop&w=1600&q=80",  # cozinha com filtro
    "https://images.unsplash.com/photo-1582719478250-96e0ef3c5a18?auto=format&fit=crop&w=1600&q=80",  # copo d'água em bancada
    "https://images.unsplash.com/photo-1526403225925-1cb2b7c0c1b0?auto=format&fit=crop&w=1600&q=80",  # jarra com água
    "https://images.unsplash.com/photo-1514996937319-344454492b37?auto=format&fit=crop&w=1600&q=80",  # água fluindo na pia
]

FALLBACK_INLINE_IMAGES = [
    "https://images.unsplash.com/photo-1530293959042-0aac487c21e3?auto=format&fit=crop&w=1400&q=80",  # detalhes de água
    "https://images.unsplash.com/photo-1502741338009-cac2772e18bc?auto=format&fit=crop&w=1400&q=80",  # gota de água
    "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?auto=format&fit=crop&w=1400&q=80",  # copos e jarra
    "https://images.unsplash.com/photo-1542744173-05336fcc7ad4?auto=format&fit=crop&w=1400&q=80",  # close de filtro
]


def _ensure_dirs() -> None:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ArticleContext:
    id: int
    source: str
    original_url: str
    title: Optional[str]
    raw_text: str
    language: Optional[str]


def _slugify(text: str) -> str:
    text = text.lower().strip()
    # remove acentos simples (não perfeito, mas suficiente)
    replacements = {
        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    slug = text or f"post-{int(datetime.now(timezone.utc).timestamp())}"
    # Limitar tamanho para evitar Errno 36 (File name too long)
    if len(slug) > MAX_SLUG_LENGTH:
        base = slug[: MAX_SLUG_LENGTH - 7].rstrip("-")
        suffix = hashlib.md5(slug.encode()).hexdigest()[:6]
        slug = f"{base}-{suffix}"
    return slug


def _download_image(url: str, dest_path: Path) -> None:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(resp.content)


def _build_frontmatter(
    title: str,
    slug: str,
    article: ArticleContext,
    image_cover_path: Optional[str],
    image_inline_path: Optional[str],
    summary: str,
    keywords: list[str],
) -> str:
    date_str = datetime.now(timezone.utc).date().isoformat()
    tags = keywords or ["água", "saúde", "filtros"]
    tags_yaml = "[" + ", ".join(f'"{t}"' for t in tags) + "]"
    # Escapar aspas para YAML (fora da f-string: backslash em f-string é inválido)
    title_escaped = title.replace('"', '\\"')
    summary_escaped = summary.replace('"', '\\"')

    frontmatter_lines = [
        "---",
        f'title: "{title_escaped}"',
        f"slug: \"{slug}\"",
        f"date: \"{date_str}\"",
        f"source: \"{article.source}\"",
        f"original_url: \"{article.original_url}\"",
        f'summary: "{summary_escaped}"',
        f"tags: {tags_yaml}",
    ]
    # Compat: manter campo image como capa
    if image_cover_path:
        frontmatter_lines.append(f"image: \"{image_cover_path}\"")
        frontmatter_lines.append(f"image_cover: \"{image_cover_path}\"")
    if image_inline_path:
        frontmatter_lines.append(f"image_inline: \"{image_inline_path}\"")
    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines)
    return frontmatter


def _write_markdown_post(
    title: str,
    slug: str,
    article: ArticleContext,
    summary: str,
    keywords: list[str],
    content_markdown: str,
    image_cover_path: Optional[str],
    image_inline_path: Optional[str],
) -> Path:
    _ensure_dirs()
    fm = _build_frontmatter(
        title,
        slug,
        article,
        image_cover_path,
        image_inline_path,
        summary,
        keywords,
    )
    body = f"{fm}\n\n{content_markdown.strip()}\n"
    path = POSTS_DIR / f"{slug}.md"
    path.write_text(body, encoding="utf-8")
    return path


def process_single_article(
    article: storage.Article,
    review_mode: str = "strict",
    generate_images: bool = True,
) -> Dict[str, Any]:
    ctx = ArticleContext(
        id=article.id,
        source=article.source,
        original_url=article.original_url,
        title=article.title,
        raw_text=article.raw_text,
        language=article.language,
    )

    print(f"  [artigo {ctx.id}] mediator_agent...", flush=True)
    mediator_result = mediator_agent.run(
        {
            "raw_text": ctx.raw_text,
            "original_title": ctx.title,
            "original_source": ctx.source,
            "language": ctx.language,
        }
    )
    print(f"  [artigo {ctx.id}] mediator ok. approved={mediator_result.get('approved')}", flush=True)

    if not mediator_result.get("approved") and review_mode == "strict":
        storage.mark_article_failed(
            ctx.id, "mediator_not_approved: " + str(mediator_result.get("review"))
        )
        return {
            "article_id": ctx.id,
            "approved": False,
            "reason": "mediator_not_approved",
        }

    final_article = mediator_result.get("final_article") or {}

    title = str(final_article.get("new_title") or ctx.title or "Artigo sobre água e saúde")
    summary = str(final_article.get("summary") or "")
    keywords = list(final_article.get("keywords") or [])
    content_markdown = str(final_article.get("content_markdown") or "")
    slug = _slugify(title)
    # Evitar sobrescrever post de outro artigo: se o slug já existe para outro article_id, tornar único.
    existing_post = storage.get_post_by_slug(slug)
    if existing_post and existing_post.get("article_id") != ctx.id:
        suffix = str(ctx.id)
        slug = f"{slug}-{suffix}" if len(slug) + 1 + len(suffix) <= MAX_SLUG_LENGTH else f"{slug[: MAX_SLUG_LENGTH - 1 - len(suffix)].rstrip('-')}-{suffix}"

    # Gera prompts de imagem (designer) e, em seguida, as imagens (quando habilitado).
    image_cover_path: Optional[str] = None
    image_inline_path: Optional[str] = None
    if generate_images:
        print(f"  [artigo {ctx.id}] image_prompt_designer...", flush=True)
        prompts = image_prompt_designer_agent.run(
            {
                "title": title,
                "summary": summary,
                "content": content_markdown,
            }
        )
        cover_prompt = str(prompts.get("cover_prompt") or "").strip() or None
        inline_prompt = str(prompts.get("inline_prompt") or "").strip() or None
        print(f"  [artigo {ctx.id}] image_agent capa...", flush=True)
        try:
            img_result = image_agent.run(
                {
                    "title": title,
                    "summary": summary,
                    "kind": "cover",
                    "prompt": cover_prompt,
                }
            )
            image_url = img_result.get("image_url")
            if image_url:
                if image_url.startswith("http"):
                    image_cover_path = image_url
                else:
                    dest = IMAGES_DIR / f"{slug}-cover.png"
                    _download_image(image_url, dest)
                    image_cover_path = f"/images/posts/{slug}-cover.png"

            print(f"  [artigo {ctx.id}] image_agent inline...", flush=True)
            # segunda imagem para o meio do texto
            img_result_inline = image_agent.run(
                {
                    "title": title,
                    "summary": summary,
                    "kind": "inline",
                    "prompt": inline_prompt,
                }
            )
            image_url_inline = img_result_inline.get("image_url")
            if image_url_inline:
                if image_url_inline.startswith("http"):
                    image_inline_path = image_url_inline
                else:
                    dest_inline = IMAGES_DIR / f"{slug}-inline.png"
                    _download_image(image_url_inline, dest_inline)
                    image_inline_path = f"/images/posts/{slug}-inline.png"
        except Exception:
            # Falha na imagem automática não impede publicação do texto.
            image_cover_path = None
            image_inline_path = None

        # Fallback fotográfico caso a geração automática não funcione.
        if image_cover_path is None and FALLBACK_COVER_IMAGES:
            idx = ctx.id % len(FALLBACK_COVER_IMAGES)
            image_cover_path = FALLBACK_COVER_IMAGES[idx]
        if image_inline_path is None and FALLBACK_INLINE_IMAGES:
            idx = (ctx.id + 1) % len(FALLBACK_INLINE_IMAGES)
            image_inline_path = FALLBACK_INLINE_IMAGES[idx]

    # Se tivermos imagem inline, inserimos no meio do texto (não logo abaixo da capa)
    if image_inline_path and content_markdown:
        blocks = content_markdown.split("\n\n")
        if len(blocks) < 2:
            content_markdown = content_markdown + "\n\n![Foto sobre água, filtros e saúde](" + image_inline_path + ")\n\n"
        else:
            # Inserir após o bloco que está em ~50% do texto
            mid = len(blocks) // 2
            before = "\n\n".join(blocks[: mid + 1])
            after = "\n\n".join(blocks[mid + 1 :])
            img_block = f"\n\n![Foto sobre água, filtros e saúde]({image_inline_path})\n\n"
            content_markdown = before + img_block + after

    post_path = _write_markdown_post(
        title=title,
        slug=slug,
        article=ctx,
        summary=summary,
        keywords=keywords,
        content_markdown=content_markdown,
        image_cover_path=image_cover_path,
        image_inline_path=image_inline_path,
    )

    storage.register_post(
        article_id=ctx.id,
        slug=slug,
        output_path=str(post_path.relative_to(PROJECT_ROOT)),
        image_path=image_cover_path,
    )
    storage.mark_article_processed(ctx.id)

    return {
        "article_id": ctx.id,
        "approved": True,
        "slug": slug,
        "post_path": str(post_path),
        "image_cover": image_cover_path,
        "image_inline": image_inline_path,
    }


def run(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Ponto de entrada principal da pipeline.

    params:
    - limit (opcional): máximo de artigos a processar nesta execução.
    """
    if params is None:
        params = {}
    limit = params.get("limit")
    review_mode = params.get("review_mode", "strict")
    status = params.get("status", "raw")
    generate_images = bool(params.get("generate_images", True))
    storage.init_db()
    _ensure_dirs()

    if status == "raw":
        articles = storage.fetch_unprocessed_articles(limit=limit)
    else:
        articles = storage.fetch_articles_by_status(status=status, limit=limit)

    total = len(articles)
    print(f"[pipeline_generate_posts] Artigos a processar: {total}", flush=True)
    if total == 0:
        print("[pipeline_generate_posts] Nenhum artigo raw. Resumo vazio.", flush=True)
        return {"total_articles": 0, "results": []}

    results = []
    for i, art in enumerate(articles):
        print(f"[pipeline_generate_posts] Processando artigo {art.id} ({i + 1}/{total})...", flush=True)
        try:
            res = process_single_article(
                art,
                review_mode=review_mode,
                generate_images=generate_images,
            )
            results.append(res)
            print(f"[pipeline_generate_posts] Artigo {art.id} concluído. approved={res.get('approved')}", flush=True)
        except Exception as exc:
            print(f"[pipeline_generate_posts] ERRO no artigo {art.id}: {exc}", flush=True)
            storage.mark_article_failed(art.id, f"pipeline_error: {exc}")
            results.append(
                {
                    "article_id": art.id,
                    "approved": False,
                    "reason": f"pipeline_exception: {exc}",
                }
            )

    summary = {
        "total_articles": total,
        "results": results,
    }
    print("[pipeline_generate_posts] resumo:", summary, flush=True)
    return summary


if __name__ == "__main__":
    run()

