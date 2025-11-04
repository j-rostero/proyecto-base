# Verificación de Conexión Frontend-Backend

## Problema: "Error de conexión con el servidor"

Este error indica que el frontend no puede conectarse al backend. Sigue estos pasos para diagnosticar y solucionar:

### 1. Verificar que el backend esté corriendo

```bash
# En una terminal, verifica que el backend esté activo
curl http://localhost:8000/api/auth/login/

# O abre en el navegador:
# http://localhost:8000/api/auth/login/
```

Si recibes un error 405 (Method Not Allowed), el backend está funcionando (ese endpoint solo acepta POST).
Si recibes un error de conexión, el backend no está corriendo.

### 2. Verificar la URL de la API

Abre la consola del navegador (F12) y verifica:
- En la página de login debería aparecer la URL de la API
- Verifica que sea: `http://localhost:8000/api`

Si no es correcta, verifica el archivo `.env.local` en el frontend:

```bash
cd frontend
cat .env.local
```

Debe contener:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### 3. Reiniciar el frontend después de cambiar .env.local

Si cambiaste el archivo `.env.local`, debes reiniciar el servidor de Next.js:

```bash
# Detén el servidor (Ctrl+C) y vuelve a iniciarlo:
cd frontend
npm run dev
```

### 4. Verificar CORS

El backend ya está configurado para permitir conexiones desde `http://localhost:3000`.
Si sigues teniendo problemas, verifica en la consola del navegador si hay errores de CORS.

### 5. Verificar puertos

- Backend debe estar en: `http://localhost:8000`
- Frontend debe estar en: `http://localhost:3000`

Si usas puertos diferentes, actualiza la configuración en `.env.local`.

### 6. Verificar logs del backend

En la terminal donde corre el backend, deberías ver las peticiones entrantes cuando intentas hacer login.

Si no ves ninguna petición, el problema es que la petición no está llegando al backend (problema de red o URL incorrecta).

### 7. Verificar en la consola del navegador

Abre la consola del navegador (F12) y busca:
- Errores de red en la pestaña Network
- Mensajes de error en la consola
- La URL que se está usando para la petición

### Solución rápida

1. Asegúrate de que ambos servidores estén corriendo:
   - Backend: `python manage.py runserver` en el directorio backend
   - Frontend: `npm run dev` en el directorio frontend

2. Verifica que el archivo `.env.local` existe y tiene el contenido correcto

3. Reinicia ambos servidores si hiciste cambios

4. Prueba hacer una petición directa al backend:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

Si esto funciona, el backend está bien y el problema está en el frontend o la configuración.

