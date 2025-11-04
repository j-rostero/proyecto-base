#!/bin/bash

# Script para iniciar el frontend Next.js

echo "Verificando node_modules..."
if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias..."
    npm install
fi

echo "Verificando archivo .env.local..."
if [ ! -f ".env.local" ]; then
    echo "Creando archivo .env.local..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
fi

echo "Iniciando servidor Next.js en http://localhost:3000..."
npm run dev

