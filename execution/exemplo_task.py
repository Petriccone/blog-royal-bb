"""
Exemplo de script da camada de Execução.

Este módulo mostra o formato sugerido para novos scripts:
- função principal `run(params: dict) -> dict`
- sem dependência direta do LLM; apenas lógica determinística
"""

from __future__ import annotations

from typing import Any, Dict

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def _init_env() -> None:
    """
    Carrega variáveis de ambiente do arquivo .env, se python-dotenv estiver instalado.
    """
    if load_dotenv is not None:
        load_dotenv()


def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ponto de entrada principal para este script de exemplo.

    :param params: Dicionário com parâmetros de entrada definidos pela diretiva.
    :return: Dicionário com resultados, pronto para ser consumido pelo agente.
    """
    _init_env()

    # Exemplo simples de processamento determinístico
    name = str(params.get("name", "mundo"))

    message = f"Olá, {name}! Este é um exemplo de script determinístico."

    result: Dict[str, Any] = {
        "ok": True,
        "message": message,
        "input_params": params,
    }

    return result


if __name__ == "__main__":
    # Pequeno teste manual:
    demo = run({"name": "Agente"})
    print(demo["message"])

