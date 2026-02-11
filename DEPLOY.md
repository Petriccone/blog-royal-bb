# Deploy — Blog Royal B&B

## Deploy do app (a partir daqui)

1. **Build (opcional, para validar):** na pasta `web` rode `npm run build`. Se passar, o app está pronto para deploy.
2. **Enviar para o GitHub:** faça commit e push do que quiser publicar (incluindo `web/`). Se o repositório estiver conectado à Vercel, o deploy é automático.
3. **Na Vercel:** confira em **Settings → General → Root Directory** que está **`web`**. Assim o Next.js usa a pasta correta.

Se preferir deploy direto pela linha de comando (sem depender do GitHub):

```bash
cd web
npx vercel --prod
```

(Só funciona se você já tiver feito `vercel login` e linkado o projeto. O comando usa a pasta `web` como raiz.)

---

## Para os artigos aparecerem no site

O site (Next.js) está em `web/`. A Vercel precisa fazer o build a partir dessa pasta.

### 1. Vercel: Root Directory

No projeto na Vercel, em **Settings → General → Root Directory** defina:

- **Root Directory:** `web`

Assim o Next.js encontra `content/posts` e as imagens em `public/images/posts`.

### 2. Subir os posts que já existem (ou novos) para o GitHub

Os posts ficam em `web/content/posts` e as imagens em `web/public/images/posts`. Para que eles entrem no repositório e o site atualize:

**Opção A – Script (recomendado)**

```bash
python -m execution.push_content_to_github
```

- Se houver alterações: faz commit e, com `PUSH_TO_GITHUB=1` e `GITHUB_TOKEN` no `.env`, faz push.
- Se não houver alterações: faz apenas `git push origin HEAD` para enviar commits que ainda não foram enviados.

**Opção B – Manual**

```bash
git add web/content/posts web/public/images/posts
git commit -m "chore: posts e imagens do blog"
git push origin main
```

Depois do push, a Vercel faz o deploy automático e os artigos passam a aparecer no site.

### 3. Onde configurar PUSH_TO_GITHUB e GITHUB_TOKEN

Para o `run_all` (ou o script de push) enviar os posts para o GitHub automaticamente:

**No seu PC (rodando `run_all` localmente):**

1. Na raiz do projeto, crie ou edite o arquivo **`.env`** (ele não vai para o Git).
2. Adicione estas linhas (troque pelo seu token real):

   ```
   PUSH_TO_GITHUB=1
   GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
   ```

**No Railway (cron que roda na nuvem):**

1. Abra o projeto no [Railway](https://railway.app) → seu serviço do blog.
2. Vá em **Variables**.
3. Clique em **Add Variable** (ou **New Variable**).
4. Crie:
   - Nome: `PUSH_TO_GITHUB`  → Valor: `1`
   - Nome: `GITHUB_TOKEN`    → Valor: seu token (ex.: `ghp_...`).

**Como criar o GITHUB_TOKEN:**

1. No GitHub: seu perfil (canto superior direito) → **Settings**.
2. No menu esquerdo: **Developer settings** → **Personal access tokens** → **Tokens (classic)**.
3. **Generate new token (classic)**.
4. Dê um nome (ex.: "Blog Royal B&B"), marque a permissão **repo** (acesso completo aos repositórios).
5. Gere e **copie o token** (começa com `ghp_`). Use esse valor em `GITHUB_TOKEN`.

Não compartilhe o token e não suba o `.env` no Git (ele já está no `.gitignore`).

### 4. Novos artigos (pipeline)

O fluxo que gera e sobe novos artigos é:

1. **Scraping** (RapidAPI) → artigos brutos no SQLite.
2. **Pipeline** (LLM + imagens) → gera os `.md` em `web/content/posts` e imagens em `web/public/images/posts`.
3. **Push** (se `PUSH_TO_GITHUB=1` e `GITHUB_TOKEN`) → commit + push no cron (Railway).

Se “nenhum artigo sobe”, confira:

- **Scraping:** logs com `429 Too Many Requests` → limite da API; aguarde ou aumente o delay em `scrape_articles.py`.
- **Pipeline:** “Artigos a processar: 0” → não há artigos com status `raw` no banco; depende do scraping.
- **Push:** confira a seção “Onde configurar PUSH_TO_GITHUB e GITHUB_TOKEN” acima; no PC também pode rodar `python -m execution.push_content_to_github` depois de gerar posts.
