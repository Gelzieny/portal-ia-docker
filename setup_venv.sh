#!/bin/bash

set -e

echo "Removendo ambiente antigo (se existir)..."
rm -rf .venv

if ! command -v pyenv &> /dev/null
then
    echo "pyenv não encontrado."
    exit 1
fi

if [ ! -f ".python-version" ]; then
    echo "Arquivo .python-version não encontrado."
    exit 1
fi

PYTHON_VERSION=$(cat .python-version)

echo "Usando Python $PYTHON_VERSION"

echo "Instalando versão caso não exista..."
pyenv install -s "$PYTHON_VERSION"

echo "Definindo versão local..."
pyenv local "$PYTHON_VERSION"

echo "Criando virtual environment..."
pyenv exec python -m venv .venv

echo "Ativando virtual environment..."
source .venv/bin/activate

echo "Atualizando pip..."
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    echo "Instalando dependências do requirements.txt..."
    pip install -r requirements.txt
else
    echo "Arquivo requirements.txt não encontrado."
fi

echo "Setup concluído. Ambiente virtual ativo."
echo "Para desativar, use: deactivate"

git update-index --assume-unchanged run.sh .env.local