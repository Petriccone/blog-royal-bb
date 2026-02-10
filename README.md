Sistema de Agente em 3 Camadas
================================

Este projeto segue a arquitetura descrita em `AGENTS.md`, separando **Diretivas**, **Orquestração** (LLM) e **Execução** (scripts determinísticos em Python).

O objetivo é ter um fluxo de trabalho confiável, em que:
- as decisões e o roteamento ficam com o agente (LLM).
- a lógica de negócio e integrações externas ficam em scripts testáveis dentro de `execution/`.
- as instruções de alto nível (SOPs) ficam documentadas em `directives/`.

## Estrutura de pastas

- `AGENTS.md` — guia de operação do agente.
- `README.md` — este arquivo, resumo do projeto.
- `directives/` — diretivas em Markdown (SOPs).
- `execution/` — scripts Python determinísticos.
- `.tmp/` — arquivos intermediários (sempre regeneráveis).
- `.env` — variáveis de ambiente, chaves de API, etc. (não versionar).
- `requirements.txt` — dependências Python usadas em `execution/`.

## Fluxo de trabalho básico

1. **Defina a tarefa em uma diretiva**
   - Crie um arquivo em `directives/`, por exemplo `directives/minha_tarefa.md`.
   - Descreva:
     - Objetivo
     - Entradas
     - Scripts de execução a usar (em `execution/`)
     - Saídas esperadas
     - Passos detalhados
     - Edge cases

2. **Implemente ou reutilize scripts em `execution/`**
   - Antes de criar um novo script, veja se já existe algo reutilizável em `execution/`.
   - Se precisar de um novo script, crie por exemplo `execution/minha_tarefa.py` com uma função principal bem definida (por exemplo, `run(params: dict) -> dict`).

3. **Use o agente para orquestrar**
   - O agente lê a diretiva em `directives/`.
   - Chama os scripts definidos na diretiva, na ordem correta, passando os parâmetros certos.
   - Lê erros, ajusta entradas/saídas e atualiza as diretivas quando necessário.

## Ambiente Python

1. Crie um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente em `.env`:

```bash
# Exemplo
GOOGLE_PROJECT_ID=
OPENAI_API_KEY=
```

## Boas práticas alinhadas ao `AGENTS.md`

- **Empurre a complexidade para os scripts** em `execution/`.
- **Atualize as diretivas** sempre que aprender algo novo (limites de API, melhores fluxos, edge cases).
- **Use `.tmp/` apenas para arquivos intermediários** que possam ser apagados a qualquer momento.
- **Segredos nunca vão para o código**: mantenha tudo em `.env`, `credentials.json` e `token.json` (ignorados pelo controle de versão).

