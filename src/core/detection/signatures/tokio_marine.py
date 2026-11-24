"""
Assinatura de detecção — Tokio Marine.

AVISO IMPORTANTE: mesmo aviso do porto_seguro.py — sem amostras reais, estes são
marcadores de partida (razão social e nome fantasia), a calibrar depois.
"""

from ..detector import InsurerSignature

TOKIO_MARINE_SIGNATURE = InsurerSignature(
    nome="Tokio Marine",
    marcadores=(
        "TOKIO MARINE SEGURADORA",
        "TOKIO MARINE",
    ),
    minimo_marcadores=1,
)
