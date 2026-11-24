import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from main import app
from core.pipeline import ParserPipeline
from PIL import Image


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"WORKSPACE_DB": str(Path(self.temp.name) / "test.sqlite3")})
        self.env.start()
        self.client = TestClient(app)
        self.account = {"name": "Teste Admin", "email": "admin@example.test", "password": "SomenteTeste123!"}
        self.assertEqual(200, self.client.post("/workspace/auth/setup", json=self.account).status_code)

    def tearDown(self):
        self.client.close()
        self.env.stop()
        self.temp.cleanup()

    def test_access_revocation_and_private_files(self):
        self.assertEqual(409, self.client.post("/workspace/auth/setup", json=self.account).status_code)
        with TestClient(app) as employee:
            for path in ["/workspace/documents", "/workspace/documents/missing/pdf", "/workspace/exports/missing"]:
                self.assertEqual(401, employee.get(path).status_code)
            self.assertEqual(401, employee.post("/excel", json={"veiculos": []}).status_code)
            member = {**self.account, "email": "employee@example.test"}
            created = self.client.post("/workspace/users", json=member).json()
            self.assertEqual(200, employee.post("/workspace/auth/login", json=member).status_code)
            self.assertEqual(403, employee.get("/workspace/users").status_code)
            self.assertEqual(200, self.client.put(f"/workspace/users/{created['id']}", json={"active": False}).status_code)
            self.assertEqual(401, employee.get("/workspace/auth/me").status_code)
            for _ in range(5):
                self.assertEqual(401, employee.post("/workspace/auth/login", json=member).status_code)
            self.assertEqual(429, employee.post("/workspace/auth/login", json=member).status_code)
        self.assertEqual(403, self.client.post("/workspace/auth/logout", headers={"Origin": "https://other.example"}).status_code)
        self.client.post("/workspace/auth/logout")
        self.assertEqual(401, self.client.get("/workspace/auth/me").status_code)

    def test_avatar_validation_persistence_and_isolation(self):
        invalid = self.client.put("/workspace/profile/avatar", files={"file": ("photo.png", b"not an image", "image/png")})
        self.assertEqual(400, invalid.status_code)
        photo = io.BytesIO()
        Image.new("RGB", (400, 200), "navy").save(photo, format="JPEG")
        result = self.client.put("/workspace/profile/avatar", files={"file": ("photo.jpg", photo.getvalue(), "image/jpeg")})
        self.assertEqual(200, result.status_code, result.text)
        version = result.json()["avatar_version"]
        self.assertTrue(version)
        self.assertEqual(version, self.client.get("/workspace/auth/me").json()["avatar_version"])
        output = self.client.get("/workspace/profile/avatar")
        self.assertEqual((256, 256), Image.open(io.BytesIO(output.content)).size)
        with TestClient(app) as other:
            self.assertEqual(401, other.get("/workspace/profile/avatar").status_code)
            member = {**self.account, "email": "other@example.test"}
            self.client.post("/workspace/users", json=member)
            other.post("/workspace/auth/login", json=member)
            self.assertEqual(404, other.get("/workspace/profile/avatar").status_code)
        self.client.post("/workspace/auth/logout")
        self.assertEqual(version, self.client.post("/workspace/auth/login", json=self.account).json()["avatar_version"])
        self.assertEqual(200, self.client.post("/workspace/profile/avatar/remove").status_code)
        self.assertEqual(404, self.client.get("/workspace/profile/avatar").status_code)

    def test_saved_revision_conflicts_and_immutable_exports(self):
        pdf = b"%PDF-1.4 test fixture"
        with patch("workspace.routes.extract", return_value={"seguradora": "Teste", "veiculos": [{"item_apolice": 1, "placa": "ABC1D23", "modelo": "ORIGINAL"}]}):
            response = self.client.post("/workspace/documents", files={"file": ("apolice.pdf", pdf, "application/pdf")})
        self.assertEqual(200, response.status_code, response.text)
        doc = response.json()
        path = f"/workspace/documents/{doc['id']}"
        self.assertEqual(pdf, self.client.get(path + "/pdf").content)
        rows = doc["veiculos"]
        rows[0]["modelo"] = "EDITADO"
        payload = {"revision": 0, "filename": "frota.xlsx", "veiculos": rows}
        saved = self.client.put(path, json=payload)
        self.assertEqual(200, saved.status_code, saved.text)
        self.assertEqual(409, self.client.put(path, json=payload).status_code)
        first = self.client.post(path + "/exports", json={"revision": 1}).json()
        binary = self.client.get(f"/workspace/exports/{first['id']}").content
        book = load_workbook(io.BytesIO(binary))
        self.assertEqual(17, book.active.max_column)
        self.assertEqual("EDITADO", book.active["D2"].value)
        rows[0]["modelo"] = "VERSAO DOIS"
        payload["revision"] = 1
        self.assertEqual(200, self.client.put(path, json=payload).status_code)
        second = self.client.post(path + "/exports", json={"revision": 2}).json()
        self.assertEqual(2, second["version"])
        self.assertEqual(binary, self.client.get(f"/workspace/exports/{first['id']}").content)
        self.assertEqual(2, len(self.client.get(path + "/history").json()["exports"]))
        self.assertNotIn("working", self.client.get("/workspace/documents").json()[0])
        with TestClient(app) as reopened:
            reopened.post("/workspace/auth/login", json=self.account)
            self.assertEqual("VERSAO DOIS", reopened.get(path).json()["veiculos"][0]["modelo"])

    def test_example_pdf_through_persistent_upload(self):
        example = Path(__file__).resolve().parents[1] / "assets/pdf-exemplos/Porto/Porto Seguro.pdf"
        if not example.exists():
            self.skipTest("PDF real de referência fica fora do repositório público")
        with patch("workspace.routes.ParserPipeline", return_value=ParserPipeline(usar_fallback_llm=False)):
            response = self.client.post("/workspace/documents", files={"file": (example.name, example.read_bytes(), "application/pdf")})
        self.assertEqual(200, response.status_code, response.text)
        self.assertEqual(17, len(response.json()["veiculos"]))


if __name__ == "__main__":
    unittest.main()
