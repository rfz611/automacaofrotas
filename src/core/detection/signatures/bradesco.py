"""
Assinatura de detecção — Bradesco Seguros.

AVISO IMPORTANTE: mesmo aviso das outras duas — marcadores de partida, a calibrar com
amostras reais.
"""

from ..detector import InsurerSignature

BRADESCO_SIGNATURE = InsurerSignature(
    nome="Bradesco Seguros",
    marcadores=(
        "BRADESCO AUTO/RE COMPANHIA DE SEGUROS",
        "BRADESCO SEGUROS",
    ),
    minimo_marcadores=1,
)
