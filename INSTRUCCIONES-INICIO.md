# Instrucciones de Inicio - Solución de Problemas con Scripts

## Problema: "source: not found" o "python: not found"

Si ves estos errores al ejecutar los scripts, sigue estas instrucciones:

## Solución Rápida

### Verificar que estás usando bash

Los scripts requieren bash. Verifica que estés usando bash:

```bash
echo $SHELL
```

Si no estás usando bash, ejecuta los scripts explícitamente con bash:

```bash
bash start-backend.sh
```

O cambia a bash:

```bash
bash
```

### Inicio Manual (Alternativa)

Si los scripts no funcionan, puedes iniciar manualmente:

**Backend:**

```bash
cd backend

# Crear entorno virtual si no existe
python3 -m venv venv

# Activar entorno virtual
. venv/bin/activate  # Nota: usa . en lugar de source

# Instalar dependencias
pip install -r requirements.txt

# Crear .env
cat > .env << EOF
SECRET_KEY=django-insecure-dev-key-change-in-production
DEBUG=True
EOF

# Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# Crear usuario de prueba
python manage.py create_test_user

# Iniciar servidor
python manage.py runserver
```

**Frontend:**

```bash
cd frontend

# Instalar dependencias
npm install

# Crear .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local

# Iniciar servidor
npm run dev
```

## Verificar Instalaciones

### Python
```bash
python3 --version
```

Si no está instalado:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Node.js
```bash
node --version
npm --version
```

Si no está instalado:
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

## Scripts Corregidos

Los scripts han sido actualizados para:
- Usar `.` en lugar de `source` (más compatible)
- Manejar rutas correctamente
- Verificar que los comandos estén disponibles
- Proporcionar mensajes de error claros

## Ejecutar Scripts

Asegúrate de dar permisos de ejecución:

```bash
chmod +x start-backend.sh
chmod +x start-frontend.sh
chmod +x iniciar-backend.sh
```

Y ejecuta con bash explícitamente si es necesario:

```bash
bash start-backend.sh
```

