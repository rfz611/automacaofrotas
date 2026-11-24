from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from core.normalizer.normalizer import Normalizer, criar_resumo_validacao
from schemas.veiculo_schema import VeiculoSchema


def veiculo(**alteracoes) -> VeiculoSchema:
    dados = {
        "item_apolice": 1,
        "placa": "ABC1D23",
        "marca": "VOLKSWAGEN",
        "modelo": "MODELO TESTE",
        "ano_fabricacao": 2020,
        "ano_modelo": 2021,
        "chassi": "9BWAA45U7FP102941",
        "classe_bonus": 0,
        "codigo_fipe": None,
        "valor_casco": None,
    }
    dados.update(alteracoes)
    return VeiculoSchema(**dados)


class ValidacaoFrotaTests(unittest.TestCase):
    def test_fipe_e_casco_ausentes_nao_exigem_revisao(self) -> None:
        normalizados = Normalizer().normalizar_lista([veiculo()])

        self.assertEqual([], normalizados[0].flags_atencao)
        self.assertEqual("APROVADO_AUTOMATICAMENTE", criar_resumo_validacao(normalizados)["status"])

    def test_chassi_invalido_e_preservado_para_revisao(self) -> None:
        normalizados = Normalizer().normalizar_lista(
            [veiculo(chassi="9BSR6X200M397067")]
        )

        self.assertEqual("9BSR6X200M397067", normalizados[0].chassi)
        self.assertEqual(["chassi"], normalizados[0].flags_atencao)

    def test_duplicidades_e_item_fora_de_sequencia_sao_sinalizados(self) -> None:
        normalizados = Normalizer().normalizar_lista(
            [
                veiculo(item_apolice=2),
                veiculo(item_apolice=2),
            ]
        )

        for extraido in normalizados:
            self.assertIn("placa_duplicada", extraido.flags_atencao)
            self.assertIn("chassi_duplicado", extraido.flags_atencao)
            self.assertIn("item_apolice_duplicado", extraido.flags_atencao)

        self.assertIn(
            "item_apolice_fora_de_sequencia", normalizados[0].flags_atencao
        )

        resumo = criar_resumo_validacao(normalizados)
        self.assertEqual("REVISAR", resumo["status"])
        self.assertEqual(2, resumo["quantidade_com_atencao"])


if __name__ == "__main__":
    unittest.main()
