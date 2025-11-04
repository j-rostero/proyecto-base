#!/bin/bash

# Script para iniciar ambos proyectos en terminales separadas

echo "=== Iniciando Backend y Frontend ==="
echo ""

# Función para iniciar backend
start_backend() {
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR/backend" || exit 1
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    . venv/bin/activate
    pip install -q -r requirements.txt
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
SECRET_KEY=django-insecure-dev-key-change-in-production
DEBUG=True
EOF
    fi
    
    python manage.py makemigrations --noinput
    python manage.py migrate --noinput
    
    # Crear usuario de prueba si no existe
    python manage.py create_test_user --username testuser --password testpass123 --email test@example.com 2>&1 | grep -q "ya existe" || echo "Usuario de prueba creado"
    
    echo "Backend Django iniciado en http://localhost:8000"
    echo "Usuario de prueba: testuser / testpass123"
    python manage.py runserver
}

# Función para iniciar frontend
start_frontend() {
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR/frontend" || exit 1
    
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    if [ ! -f ".env.local" ]; then
        cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api
EOF
    fi
    
    echo "Frontend Next.js iniciado en http://localhost:3000"
    npm run dev
}

# Iniciar backend en background
start_backend &
BACKEND_PID=$!

# Esperar un poco para que el backend inicie
sleep 3

# Iniciar frontend en background
start_frontend &
FRONTEND_PID=$!

echo ""
echo "Procesos iniciados:"
echo "  Backend PID: $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "Para detener los servidores:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Esperar a que ambos procesos terminen
wait

