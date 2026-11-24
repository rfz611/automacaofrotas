"""
Validador de duplicidade — RN-04: "alertar o usuário se houver mais de um veículo com
a mesma placa ou chassi dentro do mesmo arquivo PDF". É um ALERTA, não um bloqueio —
por isso retorna flags para exibição no Preview, nunca lança exceção nem remove itens.

Diferente de placa_validator/chassi_validator, este precisa da LISTA inteira (não dá
pra saber se algo é duplicado olhando um único veículo isolado), por isso depende de
VeiculoSchema.
"""

from __future__ import annotations

from collections import defaultdict

from schemas.veiculo_schema import VeiculoSchema


def encontrar_duplicados(veiculos: list[VeiculoSchema]) -> dict[int, list[str]]:
    """Retorna {índice_na_lista: [motivos]} para veículos cuja placa ou chassi se
    repete em outro item da MESMA lista (= mesmo PDF). Ignora placa/chassi None
    (nulo não conta como duplicata de outro nulo)."""
    indices_por_placa: dict[str, list[int]] = defaultdict(list)
    indices_por_chassi: dict[str, list[int]] = defaultdict(list)

    for indice, veiculo in enumerate(veiculos):
        if veiculo.placa:
            indices_por_placa[veiculo.placa].append(indice)
        if veiculo.chassi:
            indices_por_chassi[veiculo.chassi].append(indice)

    resultado: dict[int, list[str]] = defaultdict(list)
    for indices in indices_por_placa.values():
        if len(indices) > 1:
            for indice in indices:
                resultado[indice].append("placa_duplicada")
    for indices in indices_por_chassi.values():
        if len(indices) > 1:
            for indice in indices:
                resultado[indice].append("chassi_duplicado")

    return dict(resultado)
