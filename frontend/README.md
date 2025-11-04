# Frontend Next.js con TypeScript

## Instalación

1. Instalar dependencias:
```bash
npm install
```

2. Configurar variables de entorno:
```bash
cp .env.local.example .env.local
```

Editar `.env.local` y configurar la URL de la API:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

3. Ejecutar el servidor de desarrollo:
```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

## Estructura

- `app/` - Páginas y rutas de Next.js
  - `login/` - Página de inicio de sesión
  - `dashboard/` - Página del dashboard (requiere autenticación)
- `lib/` - Utilidades y servicios
  - `api.ts` - Cliente API con Axios
  - `auth.ts` - Servicio de autenticación

## Características

- Autenticación con JWT
- Gestión de sesión en localStorage
- Protección de rutas
- Interfaz moderna y responsive

