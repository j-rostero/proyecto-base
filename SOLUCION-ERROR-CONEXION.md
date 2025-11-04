# Solución: Error de Conexión con el Servidor

## El Error

Si ves este mensaje:
```
Error de conexión con el servidor. Verifica que el backend esté corriendo en http://localhost:8000/api
```

Significa que el frontend no puede conectarse al backend.

## Solución Paso a Paso

### Paso 1: Verificar que el Backend esté Corriendo

Abre una terminal y ejecuta:

```bash
curl http://localhost:8000/api/auth/login/
```

**Si el backend está corriendo:**
- Verás un error 405 (Method Not Allowed) - esto es NORMAL, significa que el servidor responde
- O verás un error 400 con JSON - esto también es NORMAL

**Si el backend NO está corriendo:**
- Verás: `curl: (7) Failed to connect to localhost port 8000`
- O: `curl: (52) Empty reply from server`

### Paso 2: Iniciar el Backend

Si el backend no está corriendo, inícialo:

**Opción A: Usar el script automático**
```bash
chmod +x iniciar-backend.sh
./iniciar-backend.sh
```

**Opción B: Inicio manual**
```bash
cd backend

# Activar entorno virtual
source venv/bin/activate

# Si no existe venv, créalo primero:
# python3 -m venv venv
# source venv/bin/activate
# pip install -r requirements.txt

# Crear .env si no existe
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

### Paso 3: Verificar que el Backend Responda

En otra terminal, verifica:

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

**Si funciona correctamente:**
Verás una respuesta JSON con `"success": true` y los tokens.

**Si no funciona:**
- Verifica que el servidor esté corriendo en la terminal
- Verifica que no haya errores en la consola del servidor Django

### Paso 4: Verificar el Frontend

1. **Verifica el archivo `.env.local`:**
   ```bash
   cd frontend
   cat .env.local
   ```
   
   Debe contener:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

2. **Si no existe o está mal, créalo:**
   ```bash
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
   ```

3. **Reinicia el frontend:**
   - Detén el servidor (Ctrl+C)
   - Inícialo de nuevo:
   ```bash
   npm run dev
   ```

### Paso 5: Verificar en el Navegador

1. Abre la página de login: http://localhost:3000
2. Abre la consola del navegador (F12)
3. Intenta hacer login
4. Verifica:
   - En la consola debería aparecer: "Intentando login en: http://localhost:8000/api/auth/login/"
   - En la pestaña Network deberías ver la petición a `/api/auth/login/`
   - Si hay un error, verás los detalles en la consola

## Verificación Rápida

Ejecuta este script para verificar todo:

```bash
chmod +x check-backend.sh
./check-backend.sh
```

## Problemas Comunes

### 1. El backend se detiene después de iniciar

**Causa:** Error en el código o falta de dependencias.

**Solución:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 2. Error: "Address already in use"

**Causa:** El puerto 8000 ya está en uso.

**Solución:**
- Busca el proceso que usa el puerto:
  ```bash
  lsof -i :8000
  ```
- Detén el proceso o usa otro puerto:
  ```bash
  python manage.py runserver 8001
  ```
- Actualiza `.env.local` en el frontend con el nuevo puerto.

### 3. Error: "ModuleNotFoundError"

**Causa:** Faltan dependencias.

**Solución:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 4. El frontend no se conecta aunque el backend funciona

**Causa:** Problema de CORS o URL incorrecta.

**Solución:**
- Verifica que `CORS_ALLOW_ALL_ORIGINS = True` esté en `backend/config/settings.py` cuando `DEBUG=True`
- Verifica que `.env.local` tenga la URL correcta
- Reinicia ambos servidores

## Checklist Final

- [ ] Backend corriendo en http://localhost:8000
- [ ] Frontend corriendo en http://localhost:3000
- [ ] Archivo `.env.local` existe y tiene la URL correcta
- [ ] Usuario de prueba creado: `testuser / testpass123`
- [ ] No hay errores en las consolas de ambos servidores
- [ ] La petición aparece en la pestaña Network del navegador

## Si Nada Funciona

1. Detén ambos servidores (Ctrl+C)
2. Elimina `frontend/.next`:
   ```bash
   rm -rf frontend/.next
   ```
3. Reinicia ambos servidores desde cero
4. Verifica los logs en ambas terminales

