import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from api.routes.excel import ExportarExcelRequest
from core.excel.excel_generator import gerar_excel_bytes
from openpyxl import load_workbook


class ExportacaoRevisadaTests(unittest.TestCase):
    def test_pendencias_e_edicoes_sao_exportadas_sem_perda(self):
        payload = ExportarExcelRequest(veiculos=[{
            "item_apolice": "revisar", "ano_fabricacao": "incerto",
            "ano_modelo": 2026, "classe_bonus": "confirmar",
            "marca": "MARCA EDITADA", "modelo": "=1+1", "codigo_fipe": "001234",
            "chassi": "9BM951102NB66668", "valor_casco": "a conferir",
            "rcf_danos_materiais": "1234.56", "app_passageiros": 0,
            "cobertura_vidros": "25000.00", "assistencia": "24h", "codigo_identificacao": "CI-02",
        }])
        wb = load_workbook(io.BytesIO(gerar_excel_bytes([v.model_dump() for v in payload.veiculos])))
        ws = wb.active
        self.assertEqual(17, ws.max_column)
        self.assertEqual("revisar", ws["A2"].value)
        self.assertEqual("incerto", ws["E2"].value)
        self.assertEqual("confirmar", ws["H2"].value)
        self.assertEqual("001234", ws["I2"].value)
        self.assertEqual("a conferir", ws["J2"].value)
        self.assertEqual(1234.56, ws["K2"].value)
        self.assertIsNone(ws["L2"].value)
        self.assertEqual(0, ws["N2"].value)
        self.assertEqual("CI-02", ws["Q2"].value)
        self.assertEqual("s", ws["D2"].data_type)


if __name__ == "__main__":
    unittest.main()
