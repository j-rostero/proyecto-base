#!/bin/bash

# Script para iniciar el backend Django

echo "Verificando entorno virtual..."
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

echo "Activando entorno virtual..."
source venv/bin/activate

echo "Instalando dependencias..."
pip install -r requirements.txt

echo "Verificando archivo .env..."
if [ ! -f ".env" ]; then
    echo "Creando archivo .env desde .env.example..."
    cp .env.example .env
fi

echo "Ejecutando migraciones..."
python manage.py makemigrations
python manage.py migrate

echo "Iniciando servidor Django en http://localhost:8000..."
python manage.py runserver

