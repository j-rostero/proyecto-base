#!/bin/bash

echo "=========================================="
echo "Verificación del Backend"
echo "=========================================="
echo ""

# Verificar si el backend está corriendo
echo "1. Verificando si el backend responde..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/auth/login/ | grep -q "40[05]"; then
    echo "✅ Backend está corriendo en http://localhost:8000"
    echo ""
    echo "Probando endpoint de login..."
    response=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
      -H "Content-Type: application/json" \
      -d '{"username":"test","password":"test"}' \
      -w "\nHTTP_CODE:%{http_code}")
    
    http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
    echo "   Código HTTP: $http_code (400 es normal para credenciales inválidas)"
else
    echo "❌ Backend NO está corriendo"
    echo ""
    echo "Para iniciar el backend:"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo "  python manage.py runserver"
    echo ""
    echo "O usa el script:"
    echo "  ./start-backend.sh"
    exit 1
fi

echo ""
echo "=========================================="
echo "Verificación completada"
echo "=========================================="

