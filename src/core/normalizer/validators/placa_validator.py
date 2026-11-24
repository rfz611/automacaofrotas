"""Validador de placa — RN-02. Função pura, sem dependência de VeiculoSchema, para
poder ser reusada tanto por schemas/veiculo_schema.py quanto por qualquer outro
consumidor futuro sem criar import circular."""

from __future__ import annotations

import re

PLACA_REGEX = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")


def normalizar_placa(placa: str | None) -> str | None:
    """RN-02: maiúscula, sem hífen/espaços. Não valida formato — só limpa."""
    if placa is None:
        return None
    return placa.upper().replace("-", "").replace(" ", "").strip()


def placa_valida(placa: str | None) -> bool:
    """RN-02: formato AAA0A00 (aceita padrão antigo e Mercosul)."""
    return bool(placa and PLACA_REGEX.match(placa))
