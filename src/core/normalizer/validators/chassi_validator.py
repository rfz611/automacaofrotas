"""Validador de chassi — RN-01. Função pura, mesmo raciocínio de placa_validator.py."""

from __future__ import annotations

import re

CHASSI_REGEX = re.compile(r"^[A-Z0-9]{17}$")


def normalizar_chassi(chassi: str | None) -> str | None:
    """Maiúscula, sem espaços. Não valida formato — só limpa."""
    if chassi is None:
        return None
    return chassi.upper().strip()


def chassi_valido(chassi: str | None) -> bool:
    """RN-01: exatamente 17 caracteres alfanuméricos."""
    return bool(chassi and CHASSI_REGEX.match(chassi))
