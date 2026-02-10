"""
Faz commit e push dos posts e imagens gerados para o GitHub.
Assim a Vercel detecta o push e redeploya o blog.

Requer variável de ambiente GITHUB_TOKEN (Personal Access Token com permissão repo).
No Railway: ative com PUSH_TO_GITHUB=1 e defina GITHUB_TOKEN.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    cwd = cwd or PROJECT_ROOT
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = (r.stdout or "").strip() + "\n" + (r.stderr or "").strip()
        return r.returncode == 0, out
    except Exception as e:
        return False, str(e)


def push_posts_to_github() -> bool:
    if not os.getenv("PUSH_TO_GITHUB", "").strip().lower() in ("1", "true", "yes"):
        print(
            "[git_push] Push desativado. Para subir posts ao site: defina PUSH_TO_GITHUB=1 e GITHUB_TOKEN no .env",
            flush=True,
        )
        return True
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        print("[git_push] PUSH_TO_GITHUB=1 mas GITHUB_TOKEN não definido. Pulando push.", flush=True)
        return False

    # Garante que estamos no repo
    ok, out = _run(["git", "status"])
    if not ok:
        print("[git_push] Não é um repositório git ou git não disponível:", out, flush=True)
        return False

    # Configura autor do commit (necessário em ambientes CI/Railway)
    _run(["git", "config", "user.email", "railway@blog-royal-bb.local"])
    _run(["git", "config", "user.name", "Railway Bot"])

    # Adiciona apenas posts e imagens
    paths = [
        "web/content/posts",
        "web/public/images/posts",
    ]
    for p in paths:
        _run(["git", "add", p])

    # Só commitamos se realmente houver alteração em posts ou imagens
    ok, out = _run(["git", "diff", "--cached", "--name-only"])
    if not ok:
        return False
    staged = [f for f in (out or "").strip().splitlines() if f]
    relevant = [f for f in staged if "content/posts" in f or "images/posts" in f]
    if not relevant:
        print("[git_push] Nenhuma alteração em posts/imagens. Nada a enviar.", flush=True)
        return True

    # Configura remote com token (HTTPS)
    remote_url = None
    ok, out = _run(["git", "remote", "get-url", "origin"])
    if ok and out.strip():
        remote_url = out.strip()
    if not remote_url or "github.com" not in remote_url:
        print("[git_push] Remote origin não parece GitHub. Pulando push.", flush=True)
        return False

    # Insere token na URL para autenticação
    if "https://" in remote_url and "@" not in remote_url:
        # https://github.com/user/repo.git -> https://TOKEN@github.com/user/repo.git
        url = remote_url.replace("https://", f"https://{token}@")
        _run(["git", "remote", "set-url", "origin", url])

    ok, out = _run(["git", "commit", "-m", "chore: novos posts do pipeline (Railway)"])
    if not ok and "nothing to commit" not in out.lower():
        print("[git_push] Falha no commit:", out, flush=True)
        return False

    ok, out = _run(["git", "push", "origin", "HEAD"])
    if not ok:
        print("[git_push] Falha no push:", out, flush=True)
        return False

    print("[git_push] Push concluído. Vercel deve redeployar em breve.", flush=True)
    return True
