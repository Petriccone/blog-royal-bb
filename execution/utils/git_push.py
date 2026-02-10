"""
Faz commit e push dos posts e imagens gerados para o GitHub.
Assim a Vercel detecta o push e redeploya o blog.

Requer: GITHUB_TOKEN (Personal Access Token com permissão repo).
No Railway (container sem .git): defina também GITHUB_REPO=owner/repo (ex: Petriccone/blog-royal-bb).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> tuple[bool, str]:
    cwd = cwd or PROJECT_ROOT
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (r.stdout or "").strip() + "\n" + (r.stderr or "").strip()
        return r.returncode == 0, out
    except Exception as e:
        return False, str(e)


def _push_from_repo(repo_path: Path, token: str) -> bool:
    """Faz add, commit e push a partir de um clone (repo_path tem .git)."""
    _run(["git", "config", "user.email", "railway@blog-royal-bb.local"], cwd=repo_path)
    _run(["git", "config", "user.name", "Railway Bot"], cwd=repo_path)
    for p in ["web/content/posts", "web/public/images/posts"]:
        _run(["git", "add", p], cwd=repo_path)
    ok, out = _run(["git", "diff", "--cached", "--name-only"], cwd=repo_path)
    if not ok:
        return False
    relevant = [f for f in (out or "").strip().splitlines() if "content/posts" in f or "images/posts" in f]
    if not relevant:
        print("[git_push] Nenhuma alteração em posts/imagens. Nada a enviar.", flush=True)
        return True
    ok, out = _run(["git", "commit", "-m", "chore: novos posts do pipeline (Railway)"], cwd=repo_path)
    if not ok and "nothing to commit" not in out.lower():
        print("[git_push] Falha no commit:", out, flush=True)
        return False
    ok, out = _run(["git", "remote", "get-url", "origin"], cwd=repo_path)
    url = out.strip() if ok and out.strip() else ""
    if url and "github.com" in url and "@" not in url:
        url = url.replace("https://", f"https://{token}@")
        _run(["git", "remote", "set-url", "origin", url], cwd=repo_path)
    elif not url:
        repo = os.getenv("GITHUB_REPO", "").strip()
        if repo:
            url = f"https://{token}@github.com/{repo}.git"
            _run(["git", "remote", "set-url", "origin", url], cwd=repo_path)
    ok, out = _run(["git", "push", "origin", "HEAD"], cwd=repo_path)
    if not ok:
        print("[git_push] Falha no push:", out, flush=True)
        return False
    print("[git_push] Push concluído. Vercel deve redeployar em breve.", flush=True)
    return True


def _clone_and_push(token: str) -> bool:
    """Container sem .git: clona o repo, copia posts/imagens, commit e push."""
    repo = os.getenv("GITHUB_REPO", "").strip()
    if not repo:
        print(
            "[git_push] Container sem .git. Defina GITHUB_REPO=owner/repo (ex: Petriccone/blog-royal-bb) no Railway.",
            flush=True,
        )
        return False
    url = f"https://{token}@github.com/{repo}.git"
    with tempfile.TemporaryDirectory(prefix="blog_push_") as tmp:
        clone_path = Path(tmp) / "repo"
        ok, out = _run(["git", "clone", "--depth", "1", url, str(clone_path)], timeout=180)
        if not ok:
            print("[git_push] Falha ao clonar:", out, flush=True)
            return False
        # Substitui posts/imagens no clone pelo conteúdo do container (build + novos)
        for rel in ["web/content/posts", "web/public/images/posts"]:
            src = PROJECT_ROOT / rel
            dst = clone_path / rel
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
        return _push_from_repo(clone_path, token)


def push_posts_to_github() -> bool:
    if not os.getenv("PUSH_TO_GITHUB", "").strip().lower() in ("1", "true", "yes"):
        print(
            "[git_push] Push desativado. Defina PUSH_TO_GITHUB=1 e GITHUB_TOKEN no .env",
            flush=True,
        )
        return True
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        print("[git_push] PUSH_TO_GITHUB=1 mas GITHUB_TOKEN não definido. Pulando push.", flush=True)
        return False

    ok, out = _run(["git", "status"])
    if not ok:
        if "not a git repository" in out.lower() or "no such file" in out.lower():
            print("[git_push] Sem .git no container. Usando clone temporário (GITHUB_REPO).", flush=True)
            return _clone_and_push(token)
        print("[git_push] Não é um repositório git ou git não disponível:", out, flush=True)
        return False

    # Repo git presente: fluxo normal
    _run(["git", "config", "user.email", "railway@blog-royal-bb.local"])
    _run(["git", "config", "user.name", "Railway Bot"])
    for p in ["web/content/posts", "web/public/images/posts"]:
        _run(["git", "add", p])
    ok, out = _run(["git", "diff", "--cached", "--name-only"])
    if not ok:
        return False
    relevant = [f for f in (out or "").strip().splitlines() if "content/posts" in f or "images/posts" in f]
    if not relevant:
        print("[git_push] Nenhuma alteração em posts/imagens. Nada a enviar.", flush=True)
        return True

    remote_url = None
    ok, out = _run(["git", "remote", "get-url", "origin"])
    if ok and out.strip():
        remote_url = out.strip()
    if not remote_url or "github.com" not in remote_url:
        print("[git_push] Remote origin não parece GitHub. Pulando push.", flush=True)
        return False
    if "https://" in remote_url and "@" not in remote_url:
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
