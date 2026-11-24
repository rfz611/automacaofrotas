import sys
from pathlib import Path

# Adiciona a pasta src e a raiz ao sys.path para resolver todos os imports
SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

for path in (str(SRC_DIR), str(ROOT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import uvicorn
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.routes import excel, health, parse
from workspace.routes import router as workspace_router, require_user

app = FastAPI(title="Automação Frotas API")


@app.middleware("http")
async def check_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if request.method not in {"GET", "HEAD", "OPTIONS"} and origin and origin not in {"http://127.0.0.1:3000", "http://localhost:3000"}:
        return JSONResponse({"detail": "Origem não autorizada."}, status_code=403)
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(parse.router, dependencies=[Depends(require_user)])
app.include_router(excel.router, dependencies=[Depends(require_user)])
app.include_router(workspace_router)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
