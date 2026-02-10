"""
Gera imagens de capa e inline para um post existente,
usando o image_agent (Fal nano-banana-pro) e atualiza o arquivo Markdown.

Uso:
  python -m execution.generate_images_for_post <slug>
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

import requests
from execution.agents import image_agent, image_prompt_designer_agent


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = PROJECT_ROOT / "web" / "content" / "posts"
IMAGES_DIR = PROJECT_ROOT / "web" / "public" / "images" / "posts"


def _read_frontmatter_and_body(path: Path) -> Tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    _, fm, body = parts
    return fm.strip(), body.lstrip("\n")


def _extract_field(fm: str, key: str) -> str:
    for line in fm.splitlines():
        if line.strip().startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def main(slug: str) -> None:
    md_path = POSTS_DIR / f"{slug}.md"
    if not md_path.exists():
        raise SystemExit(f"Post não encontrado: {md_path}")

    fm, body = _read_frontmatter_and_body(md_path)
    title = _extract_field(fm, "title") or slug
    summary = _extract_field(fm, "summary") or ""

    # Usa o agente de design para criar prompts específicos, evitando imagens
    # com produtos e aproximando melhor o visual do conteúdo do artigo.
    prompts = image_prompt_designer_agent.run(
        {
            "title": title,
            "summary": summary,
            "content": body,
        }
    )
    cover_prompt = str(prompts.get("cover_prompt") or "").strip() or None
    inline_prompt = str(prompts.get("inline_prompt") or "").strip() or None

    # Gera capa
    cover = image_agent.run(
        {
            "title": title,
            "summary": summary,
            "kind": "cover",
            "prompt": cover_prompt,
        }
    )
    cover_url = cover.get("image_url")

    # Gera inline
    inline = image_agent.run(
        {
            "title": title,
            "summary": summary,
            "kind": "inline",
            "prompt": inline_prompt,
        }
    )
    inline_url = inline.get("image_url")

    # Faz download das imagens geradas, se houver
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    if cover_url:
        resp = requests.get(cover_url, timeout=120)
        resp.raise_for_status()
        (IMAGES_DIR / f"{slug}-cover.png").write_bytes(resp.content)
    if inline_url:
        resp = requests.get(inline_url, timeout=120)
        resp.raise_for_status()
        (IMAGES_DIR / f"{slug}-inline.png").write_bytes(resp.content)

    # Atualiza frontmatter manualmente com caminhos locais esperados
    new_fm_lines = []
    for line in fm.splitlines():
        if line.strip().startswith("image:") or line.strip().startswith(
            "image_cover:"
        ) or line.strip().startswith("image_inline:"):
            continue
        new_fm_lines.append(line)

    if cover_url:
        new_fm_lines.append(f'image: "/images/posts/{slug}-cover.png"')
        new_fm_lines.append(f'image_cover: "/images/posts/{slug}-cover.png"')
    if inline_url:
        new_fm_lines.append(f'image_inline: "/images/posts/{slug}-inline.png"')

    new_fm = "\n".join(new_fm_lines)

    # Garante bloco de imagem inline no corpo
    if inline_url:
        # Substitui qualquer imagem anterior com o mesmo alt text por esta nova
        marker = "![Ilustração sobre água, filtros e saúde]"
        new_image_md = (
            f"{marker}(/images/posts/{slug}-inline.png)"
        )
        lines = body.splitlines()
        replaced = False
        for i, line in enumerate(lines):
            if line.strip().startswith(marker):
                lines[i] = new_image_md
                replaced = True
        if not replaced:
            new_lines = []
            inserted = False
            for line in lines:
                new_lines.append(line)
                if not inserted and line.lstrip().startswith("## "):
                    new_lines.append("")
                    new_lines.append(new_image_md)
                    new_lines.append("")
                    inserted = True
            if not inserted:
                new_lines.append("")
                new_lines.append(new_image_md)
            lines = new_lines
        body = "\n".join(lines)

    final_text = f"---\n{new_fm}\n---\n\n{body.strip()}\n"
    md_path.write_text(final_text, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Uso: python -m execution.generate_images_for_post <slug>")
    main(sys.argv[1])

