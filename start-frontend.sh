#!/bin/bash

# Script para iniciar el frontend Next.js
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/frontend" || exit 1

echo "=== Configurando Frontend Next.js ==="

# Instalar dependencias si no existen
if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias..."
    npm install
fi

# Crear .env.local si no existe
if [ ! -f ".env.local" ]; then
    echo "Creando archivo .env.local..."
    cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api
EOF
fi

echo ""
echo "=== Frontend Next.js iniciado ==="
echo "Aplicación disponible en: http://localhost:3000"
echo ""

# Iniciar servidor
npm run dev

