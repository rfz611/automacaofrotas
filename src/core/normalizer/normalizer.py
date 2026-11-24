"""
Normalizer — orquestra as regras que só fazem sentido olhando a LISTA inteira de
veículos de um PDF (RN-04, numeração sequencial), consolidando com as flags
campo-a-campo que cada VeiculoSchema já calcula sozinho (RN-01, RN-02, obrigatórios —
ver schemas/veiculo_schema.py).

RCF/DMO não recebem defaults: os limites pertencem à proposta e valores ausentes
permanecem nulos para revisão humana.
"""

from __future__ import annotations

from pydantic import Field

from schemas.veiculo_schema import VeiculoSchema

from .validators.duplicidade_validator import encontrar_duplicados


class VeiculoExtraido(VeiculoSchema):
    """VeiculoSchema + flags_atencao consolidado (campo a campo + RN-04). Formato usado
    na resposta do endpoint /parse — espelha API.md (veiculos[].flags_atencao)."""

    flags_atencao: list[str] = Field(default_factory=list)


class Normalizer:
    def normalizar_lista(self, veiculos_brutos: list[VeiculoSchema]) -> list[VeiculoExtraido]:
        duplicados = encontrar_duplicados(veiculos_brutos)
        indices_por_item: dict[int, list[int]] = {}
        for indice, veiculo in enumerate(veiculos_brutos):
            if veiculo.item_apolice is not None:
                indices_por_item.setdefault(veiculo.item_apolice, []).append(indice)

        itens_duplicados = {
            indice
            for indices in indices_por_item.values()
            if len(indices) > 1
            for indice in indices
        }
        resultado: list[VeiculoExtraido] = []

        for indice, veiculo in enumerate(veiculos_brutos):
            flags = list(veiculo.calcular_flags_atencao())

            # numera sequencialmente quando ausente (Parser-Engine.md: "numérico
            # sequencial") — campo posicional/derivável, diferente dos demais 16
            # campos, que nunca são inferidos, só extraídos ou deixados null.
            if veiculo.item_apolice is None:
                veiculo = veiculo.model_copy(update={"item_apolice": indice + 1})
                if "item_apolice" in flags:
                    flags.remove("item_apolice")

            if indice in itens_duplicados:
                flags.append("item_apolice_duplicado")
            if veiculo.item_apolice != indice + 1:
                flags.append("item_apolice_fora_de_sequencia")

            for motivo in duplicados.get(indice, []):
                if motivo not in flags:
                    flags.append(motivo)

            resultado.append(VeiculoExtraido(**veiculo.model_dump(), flags_atencao=flags))

        return resultado


def criar_resumo_validacao(veiculos: list[VeiculoExtraido]) -> dict:
    """Resume apenas as exceções que exigem conferência humana."""
    itens_com_atencao = [
        {
            "item_apolice": veiculo.item_apolice,
            "placa": veiculo.placa,
            "flags_atencao": veiculo.flags_atencao,
        }
        for veiculo in veiculos
        if veiculo.flags_atencao
    ]
    return {
        "status": "REVISAR" if itens_com_atencao else "APROVADO_AUTOMATICAMENTE",
        "quantidade_veiculos": len(veiculos),
        "quantidade_com_atencao": len(itens_com_atencao),
        "itens_com_atencao": itens_com_atencao,
    }
