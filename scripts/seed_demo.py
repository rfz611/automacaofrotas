"""Cria um banco de DEMONSTRAÇÃO com dados 100% fictícios.

Uso (na raiz do projeto):
    .venv\\Scripts\\python.exe scripts\\seed_demo.py

Gera data/demo.sqlite3 (apaga e recria). Nenhum dado real de cliente é usado:
seguradoras, empresas, placas e chassis são inventados.
Conta de acesso da demonstração: demo@frotas.local / demonstracao-frotas
"""
import json
import os
import random
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "demo.sqlite3"
os.environ["WORKSPACE_DB"] = str(DB)
sys.path.insert(0, str(ROOT / "src"))

for suffix in ("", "-wal", "-shm"):
    Path(str(DB) + suffix).unlink(missing_ok=True)

from workspace.store import database, encode, password_hash  # noqa: E402

random.seed(2026)
LETTERS = "ABCDEFGHJKLMNPRSTUVWXYZ"
VIN_CHARS = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
MODELS = [
    ("FIAT", "Strada Freedom 1.3 Flex CD"), ("FIAT", "Fiorino Endurance 1.4"),
    ("VOLKSWAGEN", "Saveiro Robust 1.6 CD"), ("VOLKSWAGEN", "Delivery 11.180"),
    ("CHEVROLET", "Montana LT 1.2 Turbo"), ("CHEVROLET", "S10 LT 2.8 Diesel 4x4"),
    ("TOYOTA", "Hilux SR 2.8 4x4 Diesel"), ("RENAULT", "Master Furgão 2.3"),
    ("FORD", "Ranger XLS 2.2 Diesel"), ("MERCEDES-BENZ", "Sprinter 416 Furgão"),
]


def placa():
    return "".join(random.choice(LETTERS) for _ in range(3)) + str(random.randint(0, 9)) + random.choice(LETTERS) + f"{random.randint(0, 99):02d}"


def chassi():
    return "9" + "".join(random.choice(VIN_CHARS) for _ in range(16))


def vehicles(count, broken):
    rows = []
    for item in range(1, count + 1):
        marca, modelo = random.choice(MODELS)
        ano = random.randint(2016, 2025)
        rows.append({
            "id": str(uuid.uuid4()), "flags_atencao": [],
            "item_apolice": item, "placa": placa(), "marca": marca, "modelo": modelo,
            "ano_fabricacao": ano, "ano_modelo": ano + random.choice([0, 0, 1]),
            "chassi": chassi(), "classe_bonus": random.randint(0, 10),
            "codigo_fipe": f"{random.randint(1, 99):03d}{random.randint(100, 999)}-{random.randint(0, 9)}",
            "valor_casco": round(random.uniform(3500, 12500), 2),
            "rcf_danos_materiais": random.choice([100000.0, 200000.0, 300000.0]),
            "rcf_danos_corporais": random.choice([100000.0, 200000.0, 300000.0]),
            "danos_morais": random.choice([10000.0, 20000.0, 50000.0]),
            "app_passageiros": random.choice([5000.0, 10000.0]),
            "cobertura_vidros": random.choice([10000.0, 15000.0, 25000.0, None]),
            "assistencia": random.choice(["24h · 500 km", "24h · 200 km", "24h · ilimitada"]),
            "codigo_identificacao": f"CI-{random.randint(100000, 999999)}",
        })
    # Casos típicos de conferência, para a demonstração mostrar o marca-texto
    if broken:
        rows[2]["chassi"] = None
        rows[5]["placa"] = "AB12C3"
        rows[8]["chassi"] = rows[7]["chassi"]
        rows[11]["ano_modelo"] = 2041
    return rows


def pdf_bytes(title):
    """PDF mínimo de uma página que diz que o documento é fictício."""
    lines = [title, "", "Documento ficticio de demonstracao.", "Nenhum dado real de cliente."]
    text = "BT /F1 16 Tf 60 760 Td 22 TL " + " ".join(f"({line}) Tj T*" for line in lines) + " ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(text)} >>\nstream\n{text}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = "%PDF-1.4\n", []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out.encode("latin-1")))
        out += f"{number} 0 obj\n{body}\nendobj\n"
    xref = len(out.encode("latin-1"))
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    return out.encode("latin-1")


DOCUMENTS = [
    ("Aurora Seguros - Transportadora Vale Azul.pdf", "Aurora Seguros", 38, True, 2),
    ("Horizonte Seguros - Logistica Pinhal.pdf", "Horizonte Seguros", 24, False, 26),
    ("Atlantica Seguros - Distribuidora Serra Verde.pdf", "Atlântica Seguros", 61, True, 50),
]

with database() as db:
    admin = {"id": str(uuid.uuid4()), "name": "Equipe Demonstração"}
    db.execute("INSERT INTO users(id,email,name,password,role,created) VALUES(?,?,?,?,?,?)",
               (admin["id"], "demo@frotas.local", admin["name"], password_hash("demonstracao-frotas"), "admin", time.time()))
    for name, email in (("Ana Ribeiro", "ana@frotas.local"), ("Bruno Matos", "bruno@frotas.local")):
        db.execute("INSERT INTO users(id,email,name,password,role,created) VALUES(?,?,?,?,?,?)",
                   (str(uuid.uuid4()), email, name, password_hash(uuid.uuid4().hex), "employee", time.time()))
    for name, insurer, count, broken, hours_ago in DOCUMENTS:
        identifier = str(uuid.uuid4())
        created = time.time() - hours_ago * 3600
        rows = vehicles(count, broken)
        db.execute("INSERT INTO documents(id,name,insurer,pdf,original,working,filename,revision,state,owner,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   (identifier, name, insurer, pdf_bytes(name[:-4]), encode(rows), encode(rows), name[:-4] + "_revisada.xlsx", 0, "EM_REVISAO", admin["id"], created, created + 120))
        for action, delta in (("PDF_RECEBIDO", 0), ("EXTRACAO_CONCLUIDA", 4)):
            db.execute("INSERT INTO events(document_id,user_id,action,details,created) VALUES(?,?,?,?,?)",
                       (identifier, admin["id"], action, json.dumps({}), created + delta))

print(f"Banco de demonstração criado em {DB}")
print("Entre com demo@frotas.local / demonstracao-frotas")
