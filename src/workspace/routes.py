import json
import io
import os
import re
import secrets
import tempfile
import time
import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from PIL import Image, ImageOps, UnidentifiedImageError

from api.routes.excel import VeiculoExportacaoSchema
from core.excel.excel_generator import gerar_excel_bytes
from core.pipeline import ParserPipeline
from workspace.review import pending_count
from workspace.store import database, encode, event, password_hash, password_valid, token_hash

router = APIRouter(prefix="/workspace")
COOKIE = "frotas_session"


def require_user(request: Request):
    token = request.cookies.get(COOKIE, "")
    with database() as db:
        user = db.execute("SELECT u.id,u.name,u.email,u.role,a.version AS avatar_version FROM sessions s JOIN users u ON u.id=s.user_id LEFT JOIN user_avatars a ON a.user_id=u.id WHERE s.token=? AND s.expires>? AND u.active=1",
                          (token_hash(token), time.time())).fetchone()
    if not user:
        raise HTTPException(401, "Sua sessão expirou. Entre novamente; a revisão salva permanece no histórico.")
    return dict(user)


def admin(user=Depends(require_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Apenas administradores podem gerenciar a equipe.")
    return user


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class NewUser(Credentials):
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=12, max_length=256)


def create_user(db, payload, role):
    email = payload.email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(400, "Informe um e-mail válido.")
    if db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
        raise HTTPException(409, "Este e-mail já possui uma conta.")
    identifier = str(uuid.uuid4())
    db.execute("INSERT INTO users(id,email,name,password,role,created) VALUES(?,?,?,?,?,?)", (identifier, email, payload.name.strip(), password_hash(payload.password), role, time.time()))
    return {"id": identifier, "email": email, "name": payload.name.strip(), "role": role}


def start_session(db, user, response):
    token = secrets.token_urlsafe(48)
    db.execute("INSERT INTO sessions VALUES(?,?,?)", (token_hash(token), user["id"], time.time() + 8 * 3600))
    response.set_cookie(COOKIE, token, httponly=True, samesite="strict", secure=os.getenv("COOKIE_SECURE") == "true", max_age=8 * 3600, path="/")


@router.get("/auth/status")
def auth_status():
    with database() as db:
        return {"setup_required": not bool(db.execute("SELECT 1 FROM users LIMIT 1").fetchone())}


@router.post("/auth/setup")
def setup(payload: NewUser, response: Response, request: Request):
    if request.client.host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(403, "A criação inicial deve ser feita localmente.")
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            raise HTTPException(409, "A conta inicial já foi criada. Faça login.")
        user = create_user(db, payload, "admin")
        start_session(db, user, response)
        event(db, user, "CONTA_INICIAL_CRIADA")
    return user


@router.post("/auth/login")
def login(payload: Credentials, response: Response):
    email = payload.email.strip().lower()
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        attempt = db.execute("SELECT * FROM login_attempts WHERE email=?", (email,)).fetchone()
        if attempt and attempt["since"] > time.time() - 300 and attempt["count"] >= 5:
            raise HTTPException(429, "Muitas tentativas. Aguarde cinco minutos.")
        row = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not row or not row["active"] or not password_valid(payload.password, row["password"]):
            count = attempt["count"] + 1 if attempt and attempt["since"] > time.time() - 300 else 1
            since = attempt["since"] if count > 1 else time.time()
            db.execute("INSERT OR REPLACE INTO login_attempts VALUES(?,?,?)", (email, count, since))
            db.commit()
            raise HTTPException(401, "E-mail ou senha incorretos.")
        user = {key: row[key] for key in ("id", "name", "email", "role")}
        avatar = db.execute("SELECT version FROM user_avatars WHERE user_id=?", (user["id"],)).fetchone()
        user["avatar_version"] = avatar["version"] if avatar else None
        db.execute("DELETE FROM login_attempts WHERE email=?", (email,))
        db.execute("DELETE FROM sessions WHERE expires<?", (time.time(),))
        start_session(db, user, response)
        event(db, user, "LOGIN")
    return user


@router.get("/auth/me")
def me(user=Depends(require_user)):
    return user


@router.get("/profile/avatar")
def avatar_image(user=Depends(require_user)):
    with database() as db:
        row = db.execute("SELECT image FROM user_avatars WHERE user_id=?", (user["id"],)).fetchone()
    if not row:
        raise HTTPException(404, "Nenhuma foto de perfil cadastrada.")
    return Response(bytes(row["image"]), media_type="image/png", headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.put("/profile/avatar")
async def update_avatar(file: UploadFile = File(...), user=Depends(require_user)):
    content = await file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(400, "Escolha uma foto de até 5 MB.")
    try:
        with Image.open(io.BytesIO(content)) as source:
            if source.format not in {"PNG", "JPEG", "WEBP"} or source.width * source.height > 16_000_000:
                raise ValueError("Formato ou dimensões inválidos")
            image = ImageOps.fit(ImageOps.exif_transpose(source).convert("RGB"), (256, 256))
            output = io.BytesIO()
            image.save(output, format="PNG")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(400, "Envie uma imagem JPG, PNG ou WebP válida de até 16 megapixels.")
    version = str(uuid.uuid4())
    with database() as db:
        db.execute("INSERT OR REPLACE INTO user_avatars VALUES(?,?,?)", (user["id"], output.getvalue(), version))
    return {**user, "avatar_version": version}


@router.post("/profile/avatar/remove")
def remove_avatar(user=Depends(require_user)):
    with database() as db:
        db.execute("DELETE FROM user_avatars WHERE user_id=?", (user["id"],))
    return {**user, "avatar_version": None}


class PasswordChange(BaseModel):
    current: str = Field(min_length=1, max_length=256)
    new: str = Field(min_length=12, max_length=256)


@router.put("/profile/password")
def change_password(payload: PasswordChange, request: Request, user=Depends(require_user)):
    """Troca a própria senha. Mantém a sessão atual e encerra as demais."""
    with database() as db:
        row = db.execute("SELECT password FROM users WHERE id=?", (user["id"],)).fetchone()
        if not row or not password_valid(payload.current, row["password"]):
            raise HTTPException(400, "A senha atual não confere.")
        if payload.current == payload.new:
            raise HTTPException(400, "A nova senha precisa ser diferente da atual.")
        db.execute("UPDATE users SET password=? WHERE id=?", (password_hash(payload.new), user["id"]))
        db.execute("DELETE FROM sessions WHERE user_id=? AND token<>?", (user["id"], token_hash(request.cookies.get(COOKIE, ""))))
        event(db, user, "SENHA_ALTERADA")
    return {"ok": True}


@router.post("/auth/logout")
def logout(request: Request, response: Response):
    with database() as db:
        db.execute("DELETE FROM sessions WHERE token=?", (token_hash(request.cookies.get(COOKIE, "")),))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/users")
def users(user=Depends(admin)):
    with database() as db:
        return [dict(row) for row in db.execute("SELECT id,name,email,role,active FROM users ORDER BY name")]


@router.post("/users")
def add_user(payload: NewUser, user=Depends(admin)):
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        member = create_user(db, payload, "employee")
        event(db, user, "FUNCIONARIO_CRIADO", details={"user_id": member["id"]})
    return member


class UserAccess(BaseModel):
    active: bool


@router.put("/users/{identifier}")
def change_access(identifier: str, payload: UserAccess, user=Depends(admin)):
    if identifier == user["id"]:
        raise HTTPException(400, "Você não pode desativar seu próprio acesso.")
    with database() as db:
        if not db.execute("SELECT 1 FROM users WHERE id=?", (identifier,)).fetchone():
            raise HTTPException(404, "Funcionário não encontrado.")
        db.execute("UPDATE users SET active=? WHERE id=?", (int(payload.active), identifier))
        if not payload.active:
            db.execute("DELETE FROM sessions WHERE user_id=?", (identifier,))
        event(db, user, "ACESSO_ATUALIZADO", details={"user_id": identifier, "active": payload.active})
    return {"ok": True}


def document(db, identifier):
    row = db.execute("SELECT * FROM documents WHERE id=?", (identifier,)).fetchone()
    if not row:
        raise HTTPException(404, "Documento não encontrado.")
    return row


def public_document(row):
    return {**{key: row[key] for key in ("id", "name", "insurer", "filename", "revision", "state", "error", "created", "updated")},
            "veiculos": json.loads(row["working"])}


def extract(path):
    result = ParserPipeline().processar(path)
    return jsonable_encoder(result)


@router.post("/documents")
async def upload(file: UploadFile = File(...), user=Depends(require_user)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Selecione uma apólice PDF.")
    content = await file.read(25 * 1024 * 1024 + 1)
    if len(content) > 25 * 1024 * 1024 or not content.startswith(b"%PDF-"):
        raise HTTPException(400, "Envie um PDF válido de até 25 MB.")
    identifier = str(uuid.uuid4())
    name = Path(file.filename.replace("\\", "/")).name[:200]
    with database() as db:
        db.execute("INSERT INTO documents(id,name,pdf,filename,state,owner,created,updated) VALUES(?,?,?,?,?,?,?,?)",
                   (identifier, name, content, name[:-4] + "_revisada.xlsx", "PROCESSANDO", user["id"], time.time(), time.time()))
        event(db, user, "PDF_RECEBIDO", identifier)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as output:
            temporary = output.name
            output.write(content)
        data = await run_in_threadpool(extract, temporary)
        rows = data.get("itens") or data.get("veiculos") or []
        if not rows:
            raise ValueError("Nenhum veículo identificado.")
        for row in rows:
            row["id"] = str(uuid.uuid4())
        with database() as db:
            db.execute("UPDATE documents SET insurer=?,original=?,working=?,state='EM_REVISAO',updated=? WHERE id=?",
                       (data.get("seguradora") or "", encode(rows), encode(rows), time.time(), identifier))
            event(db, user, "EXTRACAO_CONCLUIDA", identifier, {"veiculos": len(rows)})
            return public_document(document(db, identifier))
    except Exception as error:
        message = str(error.detail) if isinstance(error, HTTPException) else "Não foi possível extrair o PDF. Confira o documento e tente uma nova importação."
        with database() as db:
            db.execute("UPDATE documents SET state='ERRO',error=?,updated=? WHERE id=?", (message, time.time(), identifier))
            event(db, user, "EXTRACAO_FALHOU", identifier)
        raise HTTPException(422, message)
    finally:
        if temporary:
            Path(temporary).unlink(missing_ok=True)


@router.get("/documents")
def list_documents(user=Depends(require_user)):
    with database() as db:
        result = []
        for row in db.execute("SELECT d.id,d.name,d.insurer,d.filename,d.revision,d.state,d.error,d.created,d.updated,d.working,u.name AS author,"
                              "(SELECT COUNT(*) FROM exports e WHERE e.document_id=d.id) AS exports,"
                              "(SELECT MAX(e.created) FROM exports e WHERE e.document_id=d.id) AS last_export "
                              "FROM documents d JOIN users u ON u.id=d.owner ORDER BY d.updated DESC LIMIT 500"):
            value = dict(row)
            rows = json.loads(value.pop("working"))
            value["vehicles"] = len(rows)
            value["pending"] = pending_count(rows)
            result.append(value)
        return result


@router.get("/documents/{identifier}")
def get_document(identifier: str, user=Depends(require_user)):
    with database() as db:
        return public_document(document(db, identifier))


@router.get("/documents/{identifier}/pdf")
def pdf(identifier: str, user=Depends(require_user)):
    with database() as db:
        row = document(db, identifier)
        return Response(bytes(row["pdf"]), media_type="application/pdf", headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(row['name'])}", "Cache-Control": "private, no-store"})


class ReviewRow(VeiculoExportacaoSchema):
    id: str = Field(min_length=1, max_length=100)
    flags_atencao: list[str] = Field(default_factory=list, max_length=40)


class SaveReview(BaseModel):
    revision: int = Field(ge=0)
    filename: str = Field(min_length=1, max_length=200)
    veiculos: list[ReviewRow] = Field(min_length=1, max_length=10000)


def safe_name(value):
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip().rstrip(".")
    return re.sub(r"(?:\.xlsx)+$", "", value, flags=re.I)[:150] + ".xlsx"


@router.put("/documents/{identifier}")
def save(identifier: str, payload: SaveReview, user=Depends(require_user)):
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        row = document(db, identifier)
        if row["revision"] != payload.revision:
            raise HTTPException(409, "Outra revisão foi salva. Reabra o documento no histórico antes de continuar; suas alterações locais não foram substituídas.")
        rows = [value.model_dump() for value in payload.veiculos]
        old = json.loads(row["working"])
        if {value["id"] for value in rows} != {value["id"] for value in old} or len(rows) != len(old):
            raise HTTPException(400, "A revisão deve manter os veículos do documento.")
        filename = safe_name(payload.filename)
        revision = row["revision"] + 1
        if rows == old and filename == row["filename"]:
            return {"revision": row["revision"]}
        previous = {value["id"]: value for value in old}
        changes = [{"vehicle": value["id"], "field": field, "before": previous[value["id"]].get(field), "after": new}
                   for value in rows for field, new in value.items() if field not in {"id", "flags_atencao"} and previous[value["id"]].get(field) != new]
        db.execute("INSERT INTO revisions VALUES(?,?,?,?,?,?,?)", (str(uuid.uuid4()), identifier, revision, encode(rows), filename, user["id"], time.time()))
        db.execute("UPDATE documents SET working=?,filename=?,revision=?,updated=? WHERE id=?", (encode(rows), filename, revision, time.time(), identifier))
        event(db, user, "REVISAO_SALVA", identifier, {"revision": revision, "changes": changes, "filename": filename})
    return {"revision": revision}


class ExportRequest(BaseModel):
    revision: int = Field(ge=0)


@router.post("/documents/{identifier}/exports")
def export(identifier: str, payload: ExportRequest, user=Depends(require_user)):
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        row = document(db, identifier)
        if payload.revision != row["revision"]:
            raise HTTPException(409, "A revisão mudou. Reabra o documento antes de exportar.")
        rows = json.loads(row["working"])
        if not rows:
            raise HTTPException(400, "Este documento ainda não possui dados extraídos.")
        content = gerar_excel_bytes(rows)
        version = db.execute("SELECT COALESCE(MAX(version),0)+1 FROM exports WHERE document_id=?", (identifier,)).fetchone()[0]
        export_id = str(uuid.uuid4())
        db.execute("INSERT INTO exports VALUES(?,?,?,?,?,?,?,?)", (export_id, identifier, version, row["revision"], row["filename"], content, user["id"], time.time()))
        event(db, user, "EXCEL_GERADO", identifier, {"version": version, "revision": row["revision"]})
    return {"id": export_id, "version": version, "filename": row["filename"]}


@router.get("/documents/{identifier}/history")
def history(identifier: str, user=Depends(require_user)):
    with database() as db:
        document(db, identifier)
        exports = [dict(row) for row in db.execute("SELECT e.id,e.version,e.revision,e.filename,e.created,u.name AS author FROM exports e JOIN users u ON u.id=e.user_id WHERE document_id=? ORDER BY version DESC", (identifier,))]
        events = [dict(row) for row in db.execute("SELECT e.action,e.details,e.created,u.name AS author FROM events e JOIN users u ON u.id=e.user_id WHERE document_id=? ORDER BY e.id DESC LIMIT 200", (identifier,))]
    return {"exports": exports, "events": events}


@router.get("/exports/{identifier}")
def download_export(identifier: str, user=Depends(require_user)):
    with database() as db:
        row = db.execute("SELECT * FROM exports WHERE id=?", (identifier,)).fetchone()
        if not row:
            raise HTTPException(404, "Exportação não encontrada.")
        return Response(bytes(row["data"]), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(row['filename'])}", "Cache-Control": "private, no-store"})
