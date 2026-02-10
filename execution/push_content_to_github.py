"""
Envia posts e imagens para o GitHub para o site (Vercel) atualizar.

Use quando quiser garantir que o conteúdo em web/content/posts e
web/public/images/posts esteja no repositório e no ar.

- Se PUSH_TO_GITHUB=1 e GITHUB_TOKEN estiver definido: faz add, commit (se houver
  alterações) e push.
- Se não: apenas faz add e commit local; você pode dar git push manualmente.

Uso: python -m execution.push_content_to_github
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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


def main() -> None:
    paths = ["web/content/posts", "web/public/images/posts"]
    for p in paths:
        _run(["git", "add", p])

    ok, out = _run(["git", "diff", "--cached", "--name-only"])
    if not ok:
        print("git diff --cached falhou:", out)
        return
    staged = [f for f in out.strip().splitlines() if f]
    if not staged:
        print("Nenhuma alteração em posts/imagens. Fazendo push do branch atual.")
        # mesmo sem commit novo, empurra o que já está commitado
        _run(["git", "config", "user.email", "blog@royal-bb.local"])
        _run(["git", "config", "user.name", "Blog Royal B&B"])
        ok, out = _run(["git", "push", "origin", "HEAD"])
        if ok:
            print("Push concluído. O site (Vercel) deve refletir o conteúdo em breve.")
        else:
            print("Falha no push:", out)
        return

    _run(["git", "config", "user.email", "blog@royal-bb.local"])
    _run(["git", "config", "user.name", "Blog Royal B&B"])
    ok, out = _run(["git", "commit", "-m", "chore: atualiza posts e imagens do blog"])
    if not ok:
        print("Falha no commit:", out)
        return

    # Tenta push: com token (CI/Railway) ou com credenciais locais (git config)
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        ok, out = _run(["git", "remote", "get-url", "origin"])
        if ok and out.strip() and "github.com" in out and "https://" in out and "@" not in out:
            url = out.strip().replace("https://", f"https://{token}@")
            _run(["git", "remote", "set-url", "origin", url])
    ok, out = _run(["git", "push", "origin", "HEAD"])
    if ok:
        print("Commit e push concluídos. O site (Vercel) deve atualizar em breve.")
    else:
        print("Falha no push:", out)
        print("Se estiver no PC: confira git credential ou use 'git push origin main' manualmente.")


if __name__ == "__main__":
    main()
