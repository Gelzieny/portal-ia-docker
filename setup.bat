@echo off
setlocal

echo Removendo ambiente antigo (se existir)...

if exist .venv (
    rmdir /s /q .venv
)

where pyenv >nul 2>nul
if %errorlevel% neq 0 (
    echo pyenv nao encontrado.
    exit /b 1
)

if not exist .python-version (
    echo Arquivo .python-version nao encontrado.
    exit /b 1
)

set /p PYTHON_VERSION=<.python-version

echo Usando Python %PYTHON_VERSION%

echo Instalando versao caso nao exista...
pyenv install -s %PYTHON_VERSION%

echo Definindo versao local...
pyenv local %PYTHON_VERSION%

echo Criando virtual environment...
python -m venv .venv

echo Ativando virtual environment...
call .venv\Scripts\activate.bat

echo Atualizando pip...
python -m pip install --upgrade pip

if exist requirements.txt (
    echo Instalando dependencias do requirements.txt...
    pip install -r requirements.txt
) else (
    echo Arquivo requirements.txt nao encontrado.
)

echo Setup concluido. Ambiente virtual ativo.
echo Para desativar, use: deactivate

git update-index --assume-unchanged run.sh .env.local

endlocal