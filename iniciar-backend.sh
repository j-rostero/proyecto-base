#!/bin/bash

echo "=========================================="
echo "Iniciando Backend Django"
echo "=========================================="
echo ""

# Cambiar al directorio del script y luego a backend
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend" || exit 1

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 no está instalado"
    exit 1
fi

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
if [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
else
    echo "❌ Error: No se pudo activar el entorno virtual"
    exit 1
fi

# Verificar que pip esté disponible
if ! command -v pip &> /dev/null; then
    echo "❌ Error: pip no está disponible después de activar el entorno virtual"
    exit 1
fi

# Instalar dependencias
echo "Verificando dependencias..."
pip install -q -r requirements.txt

# Crear .env si no existe
if [ ! -f ".env" ]; then
    echo "Creando archivo .env..."
    cat > .env << EOF
SECRET_KEY=django-insecure-dev-key-change-in-production
DEBUG=True
EOF
fi

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py makemigrations --noinput 2>/dev/null
python manage.py migrate --noinput

# Crear usuario de prueba si no existe
echo "Verificando usuario de prueba..."
python manage.py create_test_user --username testuser --password testpass123 --email test@example.com 2>&1 | grep -q "ya existe" || echo "Usuario de prueba creado"

echo ""
echo "=========================================="
echo "Backend iniciado"
echo "=========================================="
echo "Servidor disponible en: http://localhost:8000"
echo "API disponible en: http://localhost:8000/api"
echo ""
echo "Usuario de prueba:"
echo "  Usuario: testuser"
echo "  Contraseña: testpass123"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo "=========================================="
echo ""

# Iniciar servidor
python manage.py runserver

