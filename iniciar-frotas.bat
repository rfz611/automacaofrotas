@echo off
chcp 65001 >nul
title Automacao de Frotas - iniciando
cd /d "%~dp0"

echo.
echo  === Automacao de Frotas ===
echo.

rem --- Encontrar o Python: prefere versoes estaveis (3.13, 3.12, 3.11) ---
set "PY="
for %%V in (3.13 3.12 3.11) do (
  if not defined PY ( py -%%V --version >nul 2>nul && set "PY=py -%%V" )
)
if not defined PY (
  py install --help >nul 2>nul
  if not errorlevel 1 (
    echo  Instalando o Python 3.13 para este projeto, so na primeira vez...
    py install 3.13
    py -3.13 --version >nul 2>nul && set "PY=py -3.13"
  )
)
if not defined PY ( py -3 --version >nul 2>nul && set "PY=py -3" )
if not defined PY ( python --version >nul 2>nul && set "PY=python" )
if not defined PY (
  echo  [ERRO] Python nao encontrado.
  echo  Instale o Python 3.13 em https://www.python.org/downloads/ e marque "Add python.exe to PATH".
  pause
  exit /b 1
)
echo  Usando: %PY%

rem --- Ambiente incompleto (sem as bibliotecas)? Apaga e refaz ---
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import uvicorn, fastapi, pdfplumber, openpyxl" >nul 2>nul
  if errorlevel 1 (
    echo  O ambiente do Python esta incompleto. Refazendo...
    rmdir /s /q .venv
  )
)

rem --- Criar o ambiente do Python na primeira vez ---
if not exist ".venv\Scripts\python.exe" (
  echo  Criando o ambiente do Python...
  %PY% -m venv .venv
  if errorlevel 1 ( echo  [ERRO] Nao foi possivel criar o .venv. & pause & exit /b 1 )
  echo  Instalando as bibliotecas da API, pode levar 1 a 2 minutos...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
  ".venv\Scripts\python.exe" -m pip install -r src\requirements.txt
  if errorlevel 1 (
    echo.
    echo  [ERRO] Falha ao instalar as bibliotecas.
    echo  Tire um print desta janela e mande para o Claude.
    pause
    exit /b 1
  )
)

rem --- Modo demonstracao: cria o banco ficticio se ainda nao existir ---
if "%NEXT_PUBLIC_DEMO%"=="1" (
  if not exist "data\demo.sqlite3" ".venv\Scripts\python.exe" scripts\seed_demo.py
)

rem --- Instalar o site na primeira vez ---
where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo  [ERRO] Node.js nao encontrado. Instale a versao LTS em https://nodejs.org e rode de novo.
  pause
  exit /b 1
)
rem Instala de novo sempre que as dependencias do site mudarem
pushd src\web
fc /b package-lock.json node_modules\.instalado.lock >nul 2>nul
if errorlevel 1 (
  echo  Instalando ou atualizando o site...
  call npm.cmd install
  if not errorlevel 1 copy /y package-lock.json node_modules\.instalado.lock >nul
)
popd

rem --- Subir API e site, cada um na sua janela ---
start "API - Frotas (porta 8000)" cmd /k ".venv\Scripts\python.exe -m uvicorn main:app --app-dir src --host 127.0.0.1 --port 8000"
start "Site - Frotas (porta 3001)" cmd /k "cd /d src\web && npm.cmd run dev -- --hostname 127.0.0.1 -p 3001"

echo  Abrindo o navegador em alguns segundos...
timeout /t 10 /nobreak >nul
start "" http://127.0.0.1:3001
echo.
echo  Pronto. Para desligar, feche as janelas "API - Frotas" e "Site - Frotas".
timeout /t 5 >nul
