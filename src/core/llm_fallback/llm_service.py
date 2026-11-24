"""
LLMService — ponto único que o restante do Parser Engine chama para o fallback de IA
(IA.md: "Fallback para API de LLM via Structured Outputs"). Tenta o provider primário
(Anthropic, por padrão) e, se falhar, tenta o secundário (OpenAI) antes de desistir.

Não decide SE deve usar o fallback — quem decide isso é o orquestrador
(core/pipeline.py), com base no resultado do parser determinístico. Este serviço só
sabe extrair via LLM quando chamado.
"""

from __future__ import annotations

from typing import Sequence

from schemas.veiculo_schema import VeiculoSchema

from .providers.base_provider import BaseLLMProvider, LLMProviderError


class TodosProvidersFalharamError(Exception):
    """Levantada quando NENHUM provider de LLM configurado conseguiu extrair dados —
    nesse ponto o Parser Engine já não tem mais o que tentar automaticamente; a linha
    inteira deve ser marcada para intervenção humana (não deve derrubar a API)."""


class LLMService:
    def __init__(self, providers: Sequence[BaseLLMProvider]):
        if not providers:
            raise ValueError("LLMService precisa de pelo menos 1 provider configurado")
        self._providers = tuple(providers)

    def extrair(self, texto_pdf: str, seguradora_detectada: str | None = None) -> list[VeiculoSchema]:
        erros: list[str] = []
        for provider in self._providers:
            try:
                resultado = provider.extrair(texto_pdf, seguradora_detectada)
                return resultado.veiculos
            except LLMProviderError as exc:
                erros.append(f"{provider.nome}: {exc}")
                continue  # tenta o próximo provider da lista

        raise TodosProvidersFalharamError(
            "Nenhum provider de LLM conseguiu extrair os dados. Tentativas: " + " | ".join(erros)
        )
