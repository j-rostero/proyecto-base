# Proyecto de Autenticación Django + Next.js

Este proyecto implementa un sistema completo de autenticación con usuario y contraseña, compuesto por un backend en Django REST Framework y un frontend en Next.js con TypeScript.

## Estructura del Proyecto

```
memos/
├── backend/          # Django REST Framework API
├── frontend/         # Next.js con TypeScript
└── documentation/    # Documentación del proyecto
```

## Inicio Rápido

### Opción 1: Usar Scripts Automáticos

**Backend (Terminal 1):**
```bash
chmod +x start-backend.sh
./start-backend.sh
```

**Frontend (Terminal 2):**
```bash
chmod +x start-frontend.sh
./start-frontend.sh
```

### Opción 2: Inicio Manual

**Backend (Django):**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# Crear archivo .env con:
# SECRET_KEY=django-insecure-dev-key-change-in-production
# DEBUG=True

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Opcional: crear usuario admin
python manage.py runserver
```

El backend estará disponible en `http://localhost:8000`

**Frontend (Next.js):**

```bash
cd frontend
npm install

# Crear archivo .env.local con:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api

npm run dev
```

El frontend estará disponible en `http://localhost:3000`

### Crear Usuario de Prueba

Para crear un usuario de prueba con credenciales predeterminadas:

```bash
cd backend
source venv/bin/activate
python manage.py create_test_user
```

Esto creará un usuario con:
- Usuario: `testuser`
- Contraseña: `testpass123`
- Email: `test@example.com`

También puedes personalizar las credenciales:
```bash
python manage.py create_test_user --username miusuario --password mipassword --email mi@email.com
```

### Nota sobre SQLite

El backend está configurado para usar SQLite por defecto (archivo `db.sqlite3` en el directorio backend). No se requiere configuración adicional de base de datos para desarrollo.

## Solución de Problemas

### Error: "Error de conexión con el servidor"

Si ves este error al intentar hacer login, el backend no está corriendo o no puede conectarse.

**Solución Rápida:**

1. **Inicia el backend:**
   ```bash
   chmod +x iniciar-backend.sh
   ./iniciar-backend.sh
   ```
   
   O manualmente:
   ```bash
   cd backend
   source venv/bin/activate
   python manage.py runserver
   ```

2. **Verifica que el backend responda:**
   ```bash
   curl http://localhost:8000/api/auth/login/
   ```
   Si ves un error 405 o 400, el backend está funcionando ✅

3. **Verifica el archivo `.env.local` en el frontend:**
   ```bash
   cd frontend
   cat .env.local
   ```
   Debe contener: `NEXT_PUBLIC_API_URL=http://localhost:8000/api`
   
   Si no existe, créalo:
   ```bash
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
   ```

4. **Reinicia el frontend** después de cambiar `.env.local`:
   ```bash
   # Detén el servidor (Ctrl+C) y reinicia:
   cd frontend
   npm run dev
   ```

5. **Verifica en la consola del navegador** (F12):
   - Busca la URL de la API que se está usando
   - Revisa errores de red en la pestaña Network

**Guía completa:** Ver `SOLUCION-ERROR-CONEXION.md` para más detalles

## Características

- ✅ Autenticación con usuario y contraseña
- ✅ Tokens JWT para sesión
- ✅ Gestión de sesión en localStorage
- ✅ Dashboard después del login
- ✅ Protección de rutas
- ✅ Interfaz moderna y responsive

## Documentación

Ver `documentation/001-proyecto-autenticacion-django-nextjs.md` para documentación detallada del proyecto.

