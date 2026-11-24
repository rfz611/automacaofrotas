@echo off
rem Abre o sistema com dados 100% ficticios (para prints e portfolio).
rem Feche antes as janelas do iniciar-frotas.bat normal, se estiverem abertas.
set "WORKSPACE_DB=%~dp0data\demo.sqlite3"
set "NEXT_PUBLIC_DEMO=1"
echo  MODO DEMONSTRACAO - entre com demo@frotas.local / demonstracao-frotas
call "%~dp0iniciar-frotas.bat"
