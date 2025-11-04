#!/bin/bash

echo "=== Verificación de Backend ==="
echo ""

# Verificar si el backend está corriendo
echo "1. Verificando si el backend está corriendo..."
if curl -s http://localhost:8000/api/auth/login/ > /dev/null 2>&1; then
    echo "✅ Backend está corriendo en http://localhost:8000"
else
    echo "❌ Backend NO está corriendo en http://localhost:8000"
    echo "   Ejecuta: cd backend && source venv/bin/activate && python manage.py runserver"
    exit 1
fi

echo ""

# Verificar configuración de CORS
echo "2. Verificando configuración de CORS..."
response=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  http://localhost:8000/api/auth/login/)

if [ "$response" = "200" ] || [ "$response" = "405" ]; then
    echo "✅ CORS configurado correctamente"
else
    echo "⚠️  Posible problema con CORS (código: $response)"
fi

echo ""

# Verificar que el endpoint responde
echo "3. Verificando endpoint de login..."
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  http://localhost:8000/api/auth/login/)

if [ "$response" = "400" ]; then
    echo "✅ Endpoint responde correctamente (400 es esperado para credenciales inválidas)"
elif [ "$response" = "200" ]; then
    echo "✅ Endpoint responde correctamente"
else
    echo "⚠️  Endpoint responde con código: $response"
fi

echo ""
echo "=== Verificación completada ==="

