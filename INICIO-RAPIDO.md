# Inicio Rápido - Levantar Proyectos

## Backend Django (Terminal 1)

Ejecuta estos comandos en una terminal:

```bash
cd backend

# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env (si no existe)
cat > .env << EOF
SECRET_KEY=django-insecure-dev-key-change-in-production
DEBUG=True
EOF

# Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# (Opcional) Crear superusuario
# python manage.py createsuperuser

# O crear un usuario de prueba rápido:
# python manage.py create_test_user

# Iniciar servidor
python manage.py runserver
```

El backend estará disponible en: **http://localhost:8000**

## Frontend Next.js (Terminal 2)

En otra terminal, ejecuta:

```bash
cd frontend

# Instalar dependencias
npm install

# Crear archivo .env.local (si no existe)
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api
EOF

# Iniciar servidor
npm run dev
```

El frontend estará disponible en: **http://localhost:3000**

## Crear Usuario de Prueba

Para crear un usuario de prueba con credenciales predeterminadas:

```bash
cd backend
source venv/bin/activate
python manage.py create_test_user
```

Esto creará un usuario con:
- **Usuario:** `testuser`
- **Contraseña:** `testpass123`
- **Email:** `test@example.com`

## Verificar que todo funciona

1. Abre tu navegador en: http://localhost:3000
2. Deberías ver la página de login
3. Usa las credenciales del usuario de prueba creado:
   - Usuario: `testuser`
   - Contraseña: `testpass123`
4. O crea un nuevo usuario desde el admin de Django: http://localhost:8000/admin

## Nota sobre SQLite

El proyecto usa SQLite por defecto. La base de datos se creará automáticamente en `backend/db.sqlite3` cuando ejecutes las migraciones. No necesitas configurar ninguna base de datos adicional.

