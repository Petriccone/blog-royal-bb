Execução (Camada 3)
===================

Os scripts em `execution/` implementam **como fazer**: são determinísticos, testáveis e lidam com APIs, arquivos, bancos de dados, etc.

## Princípios

- Cada script deve ter uma **responsabilidade clara**.
- Evite lógica complexa no agente; coloque aqui.
- Sempre que possível, centralize integrações externas em funções reutilizáveis.

## Ponto de entrada sugerido

Uma convenção simples é expor uma função `run` em cada script:

```python
def run(params: dict) -> dict:
    """
    Executa a tarefa principal do script.

    :param params: Dicionário com parâmetros de entrada.
    :return: Dicionário com resultados e metadados.
    """
    ...
```

## Boas práticas

- Use `.env` para credenciais e configurações, carregando com `python-dotenv`.
- Não grave segredos em arquivos dentro de `execution/`.
- Use `.tmp/` para arquivos intermediários que possam ser apagados a qualquer momento.

