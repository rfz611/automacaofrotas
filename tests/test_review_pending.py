import unittest

from src.workspace.review import pending_count


def vehicle(item, placa, chassi, **extra):
    base = {"item_apolice": item, "placa": placa, "marca": "FIAT", "modelo": "STRADA", "ano_fabricacao": 2022,
            "ano_modelo": 2023, "chassi": chassi, "classe_bonus": 5}
    return {**base, **extra}


class PendingCountTest(unittest.TestCase):
    """Mesmas regras da tela de revisão (src/web/lib/review.ts)."""

    def test_clean_fleet_has_no_pending(self):
        rows = [vehicle(1, "ABC1D23", "9BD281B3CNYX63336"), vehicle(2, "ABC1234", "9BD281B3CNYX63530")]
        self.assertEqual(pending_count(rows), 0)

    def test_each_problem_counts_one_cell(self):
        rows = [
            vehicle(1, "AB12C3", "9BD281B3CNYX6333"),           # placa e chassi inválidos = 2
            vehicle(2, "ABC1234", "9BD281B3CNYX63530", marca=None),  # marca vazia + placa repetida (com a linha 3) = 2
            vehicle(3, "ABC1234", "9BD281B3CNYX63531", ano_modelo=2041),  # placa repetida + ano modelo = 2
            vehicle(4, "XYZ9876", "9BD281B3CNYX63532", flags_atencao=["valor_casco_ausente"]),  # aviso do leitor = 1
        ]
        self.assertEqual(pending_count(rows), 7)


if __name__ == "__main__":
    unittest.main()
