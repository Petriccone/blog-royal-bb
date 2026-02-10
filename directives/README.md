Diretivas (Camada 1)
=====================

As diretivas definem **o que fazer**. São SOPs em Markdown que moram dentro de `directives/`.

Cada diretiva deve:
- Explicar claramente o **objetivo**.
- Listar as **entradas** (parâmetros, arquivos, credenciais necessárias).
- Referenciar os **scripts em `execution/`** que serão usados.
- Descrever as **saídas esperadas**.
- Trazer **passos detalhados** para o agente seguir.
- Mapear **edge cases** e erros comuns.

## Estrutura sugerida de uma diretiva

Use este modelo para novas diretivas:

```markdown
# Nome da tarefa

## Objetivo
Descreva o que deve ser alcançado.

## Entradas
- **entrada_1**: descrição
- **entrada_2**: descrição

## Scripts de execução
- `execution/exemplo_task.py` — o que ele faz, principais parâmetros e saídas.

## Saídas esperadas
- Arquivo/planilha/registro gerado
- Logs importantes

## Passos detalhados
1. Passo 1...
2. Passo 2...
3. ...

## Edge cases
- Caso X: como lidar
- Caso Y: como lidar

## Observações
- Notas adicionais, limites de API, tempo esperado, etc.
```

## Boas práticas

- Antes de criar uma nova diretiva, veja se já existe algo parecido que possa ser reaproveitado ou ajustado.
- Sempre que descobrir um novo problema, limite de API ou melhoria de fluxo, **volte aqui e atualize a diretiva correspondente**.

