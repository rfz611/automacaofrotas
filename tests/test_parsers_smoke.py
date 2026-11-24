from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from core.excel.excel_generator import gerar_excel_bytes
from core.parsers.bradesco_parser import BradescoParser
from core.parsers.porto_seguro_parser import PortoParser
from core.parsers.sura_parser import SuraParser


class ParserSmokeTests(unittest.TestCase):
    def verificar(self, parser, caminho: Path, quantidade_esperada: int) -> None:
        if not caminho.exists():
            self.skipTest("PDF real de referência fica fora do repositório público")
        resultado = parser.parse(caminho_pdf=str(caminho))
        itens = resultado.get("itens", [])

        self.assertEqual(quantidade_esperada, len(itens))
        self.assertGreater(len(gerar_excel_bytes(itens)), 0)

    def test_bradesco(self) -> None:
        self.verificar(
            BradescoParser(),
            ROOT / "assets/pdf-exemplos/Bradesco/Bradesco.PDF",
            152,
        )

    def test_porto_seguro(self) -> None:
        self.verificar(
            PortoParser(),
            ROOT / "assets/pdf-exemplos/Porto/Porto Seguro.pdf",
            17,
        )

    def test_porto_seguro_frota_grande(self) -> None:
        self.verificar(
            PortoParser(),
            ROOT / "assets/pdf-exemplos/Porto/Porto Seguro 2.PDF",
            100,
        )

    def test_sura(self) -> None:
        self.verificar(
            SuraParser(),
            ROOT / "assets/pdf-exemplos/Sura/Sura.pdf",
            42,
        )


if __name__ == "__main__":
    unittest.main()
