@echo off
chcp 65001 >nul
title Redefinir senha - Automacao de Frotas
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Rode primeiro o iniciar-frotas.bat para instalar o sistema.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\redefinir_senha.py
echo.
pause
