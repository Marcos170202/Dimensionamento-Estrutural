"""Parsing de texto compartilhado entre ``model_tab``/``checks_tab``.

So a conversao numerica de baixo nivel (aceitar virgula OU ponto como
separador decimal) mora aqui — cada modulo chamador decide como
envolver um erro de parsing na excecao/mensagem que faz sentido no seu
contexto (``ModelInputError`` com linha/tabela em ``model_tab``, um
``ValueError`` simples com o nome do campo em ``checks_tab``), entao
nao ha uma funcao publica unica de "parse com mensagem de erro" — so a
conversao em si, para nao duplicar ``text.replace(",", ".")`` +
``float(...)`` nos dois lugares.
"""

from __future__ import annotations


def parse_decimal(text: str) -> float:
    """Converte texto para ``float``, aceitando ``,`` OU ``.`` como separador decimal.

    Levanta ``ValueError`` (mensagem padrao do ``float()``) se o texto
    nao for um numero valido apos a substituicao — o chamador decide
    como envolver isso num erro com mais contexto.
    """
    return float(text.replace(",", "."))
