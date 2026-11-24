import re


class PortoSignature:
    nome = "Porto Seguro"

    @classmethod
    def matches(cls, texto: str) -> bool:
        texto_limpo = re.sub(r'\(cid:\d+\)', '', texto)
        padroes = [
            r'PORTO\s*SEGURO\s*COMPANHIA\s*DE\s*SEGUROS',
            r'porto\s*seguro',
            r'po\(cid:1\)o\s*seguro',
            r'Seguro\s*Auto\s*Frota',
            r'CAMPODORO\s*TRANSPORTES',
        ]
        score = sum(1 for p in padroes if re.search(p, texto_limpo, re.IGNORECASE))
        return score >= 2


# Disponibiliza com ambos os nomes para evitar qualquer conflito de import
PORTO_SIGNATURE = PortoSignature()
PORTO_SEGURO_SIGNATURE = PORTO_SIGNATURE