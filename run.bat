@echo off

echo Ativando ambiente virtual...
call .venv\Scripts\activate

echo Iniciando servidor...
uvicorn app.main:app --host 127.0.0.1 --port 5090 --log-level debug --reload

echo Desativando ambiente virtual...
deactivate
