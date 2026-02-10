"""
Revisa imagens de TODOS os posts existentes.

Fluxo:
- Para cada arquivo em `web/content/posts/*.md`:
  - Lê título, resumo e corpo.
  - Pede para o `image_prompt_designer_agent` gerar prompts (capa + inline),
    usando o conteúdo completo do artigo.
  - Usa o `image_agent` para gerar novas imagens de capa e inline.
  - Salva as imagens em `web/public/images/posts/<slug>-cover.png` e
    `.../<slug>-inline.png`.
  - Atualiza o frontmatter com `image`, `image_cover` e `image_inline`.
  - Garante que exista UMA imagem inline no corpo, alinhada ao novo arquivo.

Na prática:
- Posts SEM imagem passam a ter imagens.
- Posts COM imagem têm as imagens refeitas com prompts mais contextuais.
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


def _download_to(path: Path, url: str) -> None:
  IMAGES_DIR.mkdir(parents=True, exist_ok=True)
  resp = requests.get(url, timeout=120)
  resp.raise_for_status()
  path.write_bytes(resp.content)


def _ensure_inline_image(body: str, slug: str) -> str:
  """
  Garante que exista UMA imagem inline com o caminho
  `/images/posts/<slug>-inline.png`.
  """
  marker = "![Ilustração sobre água, filtros e saúde]"
  new_image_md = f"{marker}(/images/posts/{slug}-inline.png)"

  lines = body.splitlines()
  replaced = False
  for i, line in enumerate(lines):
    if line.strip().startswith(marker):
      lines[i] = new_image_md
      replaced = True
  if replaced:
    return "\n".join(lines)

  # não havia marcador anterior → insere após o primeiro subtítulo ou no fim
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
  return "\n".join(new_lines)


def process_post(md_path: Path) -> None:
  slug = md_path.stem
  fm, body = _read_frontmatter_and_body(md_path)
  title = _extract_field(fm, "title") or slug
  summary = _extract_field(fm, "summary") or ""

  # 1) Designer de prompt avalia o texto e gera prompts
  prompts = image_prompt_designer_agent.run(
    {
      "title": title,
      "summary": summary,
      "content": body,
    }
  )
  cover_prompt = str(prompts.get("cover_prompt") or "").strip() or None
  inline_prompt = str(prompts.get("inline_prompt") or "").strip() or None

  # 2) Geração de capa
  cover = image_agent.run(
    {
      "title": title,
      "summary": summary,
      "kind": "cover",
      "prompt": cover_prompt,
    }
  )
  cover_url = cover.get("image_url")

  # 3) Geração de inline
  inline = image_agent.run(
    {
      "title": title,
      "summary": summary,
      "kind": "inline",
      "prompt": inline_prompt,
    }
  )
  inline_url = inline.get("image_url")

  IMAGES_DIR.mkdir(parents=True, exist_ok=True)

  if cover_url:
    _download_to(IMAGES_DIR / f"{slug}-cover.png", cover_url)
  if inline_url:
    _download_to(IMAGES_DIR / f"{slug}-inline.png", inline_url)

  # 4) Atualiza frontmatter manualmente com caminhos locais esperados
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

  # 5) Garante bloco de imagem inline no corpo
  if inline_url:
    body = _ensure_inline_image(body, slug)

  final_text = f"---\n{new_fm}\n---\n\n{body.strip()}\n"
  md_path.write_text(final_text, encoding="utf-8")

  print(f"[review_images_for_all_posts] Atualizado: {md_path.name}")


def main() -> None:
  if not POSTS_DIR.exists():
    print(f"Nenhum diretório de posts encontrado em {POSTS_DIR}")
    return

  md_files = sorted(POSTS_DIR.glob("*.md"))
  if not md_files:
    print(f"Nenhum post encontrado em {POSTS_DIR}")
    return

  for path in md_files:
    try:
      process_post(path)
    except Exception as exc:  # noqa: BLE001
      print(f"[review_images_for_all_posts] Erro ao processar {path.name}: {exc}")


if __name__ == "__main__":
  main()

