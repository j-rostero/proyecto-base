#!/bin/bash

# Script para crear un usuario de prueba

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend" || exit 1

# Activar entorno virtual si existe
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
fi

# Ejecutar migraciones si es necesario
if [ ! -f "db.sqlite3" ]; then
    echo "Ejecutando migraciones..."
    python manage.py makemigrations
    python manage.py migrate
fi

# Crear usuario de prueba
echo "Creando usuario de prueba..."
python manage.py create_test_user

echo ""
echo "Usuario de prueba creado:"
echo "  Usuario: testuser"
echo "  Contraseña: testpass123"
echo "  Email: test@example.com"

