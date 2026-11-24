import os
import re
from typing import List, Optional, Union, Any
import pdfplumber


def limpar_texto_duplicado(texto: str) -> str:
    """Remove sobreposição de caracteres do PDF (ghost text) e tags (cid:x)."""
    if not texto:
        return ""
    
    # Remove codificação de fontes embutidas (comum na Porto Seguro)
    texto = re.sub(r'\(cid:\d+\)', '', texto)

    lines = []
    for line in texto.splitlines():
        if len(line) >= 4:
            pares_duplicados = [line[i] == line[i+1] for i in range(0, len(line) - 1, 2)]
            if pares_duplicados and (sum(pares_duplicados) / len(pares_duplicados)) > 0.6:
                line = line[::2]
        lines.append(line)
    return "\n".join(lines)


class InsurerSignature:
    def __init__(self, nome: str = "", marcadores: Optional[List[str]] = None, minimo_marcadores: int = 1, **kwargs):
        self.nome = nome
        self.marcadores = marcadores or []
        self.minimo_marcadores = minimo_marcadores
        for k, v in kwargs.items():
            setattr(self, k, v)

    def matches(self, text: str) -> bool:
        if not self.marcadores:
            return self.nome.upper() in text.upper()
        texto_upper = text.upper()
        encontrados = sum(1 for m in self.marcadores if m.upper() in texto_upper)
        return encontrados >= self.minimo_marcadores


class ResultadoDeteccao:
    def __init__(self, seguradora: str, texto_limpo: str = "", confianca: float = 1.0):
        self.seguradora = seguradora
        self.nome = seguradora
        self.texto_limpo = texto_limpo
        self.confianca = confianca

    def upper(self) -> str:
        return self.seguradora.upper()

    def strip(self) -> str:
        return self.seguradora.strip()

    def __str__(self):
        return self.seguradora

    def __repr__(self):
        return f"<ResultadoDeteccao seguradora='{self.seguradora}'>"


class Detector:
    def __init__(self, signatures: Optional[List[Any]] = None):
        if signatures is None:
            self.signatures = []
            try:
                from core.detection.signatures.bradesco import BRADESCO_SIGNATURE
                self.signatures.append(BRADESCO_SIGNATURE)
            except Exception:
                pass

            try:
                from core.detection.signatures.porto_seguro import PORTO_SIGNATURE
                self.signatures.append(PORTO_SIGNATURE)
            except Exception:
                pass

            try:
                from core.detection.signatures.sura import SURA_SIGNATURE
                self.signatures.append(SURA_SIGNATURE)
            except Exception:
                pass
        else:
            self.signatures = signatures

    def extrair_texto(self, caminho_pdf: str, max_paginas: Optional[int] = None) -> str:
        paginas_limpas = []
        with pdfplumber.open(caminho_pdf) as pdf:
            paginas = pdf.pages if max_paginas is None else pdf.pages[:max_paginas]
            for page in paginas:
                raw_text = page.extract_text() or ""
                paginas_limpas.append(limpar_texto_duplicado(raw_text))
        return "\n".join(paginas_limpas)

    def detectar(self, texto_ou_caminho: str) -> ResultadoDeteccao:
        if isinstance(texto_ou_caminho, str) and os.path.exists(texto_ou_caminho):
            texto = self.extrair_texto(texto_ou_caminho, max_paginas=5)
        else:
            texto = limpar_texto_duplicado(texto_ou_caminho or "")

        seguradora_nome = "DESCONHECIDO"
        for sig in self.signatures:
            if hasattr(sig, 'matches') and sig.matches(texto):
                seguradora_nome = sig.nome
                break

        if seguradora_nome == "DESCONHECIDO":
            texto_upper = texto.upper()
            if "BRADESCO" in texto_upper:
                seguradora_nome = "Bradesco Seguros"
            elif "PORTO" in texto_upper:
                seguradora_nome = "Porto Seguro"
            elif "SURA" in texto_upper:
                seguradora_nome = "Seguros Sura"

        return ResultadoDeteccao(seguradora=seguradora_nome, texto_limpo=texto)