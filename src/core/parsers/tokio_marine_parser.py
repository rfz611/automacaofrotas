"""Parser determinístico — Tokio Marine. Mesma lógica compartilhada de BaseParser."""

from core.detection.signatures.tokio_marine import TOKIO_MARINE_SIGNATURE

from .base_parser import BaseParser


class TokioMarineParser(BaseParser):
    seguradora = TOKIO_MARINE_SIGNATURE.nome

    def consegue_processar(self, texto_pdf: str) -> bool:
        texto_upper = texto_pdf.upper()
        return any(m.upper() in texto_upper for m in TOKIO_MARINE_SIGNATURE.marcadores)
