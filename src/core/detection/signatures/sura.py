import re


class SuraSignature:
    nome = "Seguros Sura"

    @classmethod
    def matches(cls, texto: str) -> bool:
        padroes = [
            r'SEGUROS\s*SURA',
            r'\bSURA\b',
            r'Seguro\s*de\s*Autom[óo]vel\s*-\s*0531',
            r'AUTO\s*FROTA\s*Proposta',
            r'Demonstrativo\s*de\s*Coberturas\s*Securit[áa]rias',
            r'Tabela\s*Molicar',
        ]
        score = sum(1 for p in padroes if re.search(p, texto, re.IGNORECASE))
        return score >= 2


SURA_SIGNATURE = SuraSignature()