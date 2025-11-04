# Implementación Completa del Sistema de Memorándums

## Resumen de Cambios

Este documento describe la implementación completa del sistema de gestión de memorándums internos según los requisitos especificados en `requisitos.md`.

## Backend (Django Rest Framework)

### 1. Modelos de Datos

#### Usuario y Roles
- Se agregó el campo `role` al modelo `User` con las siguientes opciones:
  - `SECONDARY_USER` (Redactor)
  - `DIRECTOR` (Aprobador)
  - `AREA_USER` (Receptor)
- El campo utiliza `TextChoices` de Django para garantizar la integridad de los datos.

#### Modelo Memo
Se creó el modelo `Memo` con los siguientes campos:
- `subject` (CharField): Asunto del memo
- `body` (TextField): Contenido principal
- `status` (CharField con Choices): Estados `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`
- `author` (ForeignKey): Usuario que crea el memo (SECONDARY_USER)
- `approver` (ForeignKey, nullable): Usuario que aprueba (DIRECTOR)
- `recipients` (ManyToManyField): Usuarios destinatarios (AREA_USER)
- `created_at` (DateTimeField): Fecha de creación
- `approved_at` (DateTimeField, nullable): Fecha de aprobación
- `parent_memo` (ForeignKey a 'self'): Para memos de respuesta
- `signed_file` (FileField): PDF final firmado
- `rejection_reason` (TextField, nullable): Motivo de rechazo

#### Modelo MemoAttachment
Se creó el modelo `MemoAttachment` para gestionar los adjuntos:
- `memo` (ForeignKey): Memo al que pertenece
- `file` (FileField): Archivo adjunto (PDF)
- `uploaded_by` (ForeignKey): Usuario que subió el archivo
- `uploaded_at` (DateTimeField): Fecha de subida

### 2. Permisos Personalizados

Se implementaron los siguientes permisos en `memos/permissions.py`:
- `IsSecondaryUser`: Permite acceso solo a usuarios con rol SECONDARY_USER
- `IsDirector`: Permite acceso solo a usuarios con rol DIRECTOR
- `IsRecipientOrInvolved`: Permite ver memos APPROVED donde el usuario es recipient o author
- `CanEditDraft`: Permite editar solo memos en estado DRAFT y solo si es el autor

### 3. Serializers

Se crearon múltiples serializers en `memos/serializers.py`:
- `MemoListSerializer`: Para listar memos (versión simplificada)
- `MemoDetailSerializer`: Para ver detalles completos de un memo
- `MemoCreateSerializer`: Para crear nuevos memos
- `MemoUpdateSerializer`: Para actualizar memos existentes
- `MemoAttachmentSerializer`: Para gestionar adjuntos

### 4. ViewSet y Endpoints de API

Se implementó un `MemoViewSet` en `memos/views.py` con las siguientes acciones:

#### Endpoints CRUD estándar:
- `GET /api/memos/`: Listar memos (con filtro por status mediante query param)
- `POST /api/memos/`: Crear nuevo memo (solo SECONDARY_USER)
- `GET /api/memos/<id>/`: Ver detalle de un memo
- `PATCH /api/memos/<id>/`: Actualizar memo (solo si status=DRAFT y es el autor)

#### Acciones personalizadas:
- `POST /api/memos/<id>/submit/`: Enviar memo a aprobación (SECONDARY_USER)
- `POST /api/memos/<id>/approve/`: Aprobar memo y generar PDF firmado (DIRECTOR)
- `POST /api/memos/<id>/reject/`: Rechazar memo (DIRECTOR)
- `POST /api/memos/<id>/reply/`: Crear memo de respuesta (RECIPIENT, DIRECTOR o AUTHOR)
- `POST /api/memos/<id>/upload_attachment/`: Subir adjunto PDF (solo si status=DRAFT)

### 5. Generación de PDF Firmado

Se implementó la función `generate_signed_pdf` en `memos/services.py` que:
1. Genera un PDF usando `reportlab` con el contenido del memo
2. Incluye información del memo (asunto, contenido, autor, aprobador, destinatarios)
3. Agrega imágenes de sello y firma (si existen en `media/seal.png` y `media/signature.png`)
4. Concatena los PDFs adjuntos usando `PyPDF2`
5. Guarda el PDF final en el campo `signed_file` del memo

### 6. Sistema de Notificaciones

Se implementaron signals en `memos/signals.py` que:
- Envían correos electrónicos cuando un memo cambia a estado `APPROVED` (notifica a recipients y autor)
- Envían correos cuando un memo cambia a estado `REJECTED` (notifica al autor con motivo)
- Envían correos cuando un memo cambia a estado `PENDING_APPROVAL` (notifica al aprobador)

### 7. Configuración

- Se agregó la app `memos` a `INSTALLED_APPS` en `settings.py`
- Se configuró `MEDIA_URL` y `MEDIA_ROOT` para manejar archivos
- Se agregaron dependencias: `reportlab`, `Pillow`, `PyPDF2`
- Se configuró el backend de email para desarrollo (console)

### 8. Endpoint de Usuarios

Se agregó `GET /api/users/` en `accounts/views.py` para listar usuarios filtrados por rol (necesario para el frontend).

## Frontend (Next.js)

### 1. Dependencias Instaladas

Se actualizó `package.json` con:
- `swr`: Para fetching y caching de datos
- `zustand`: Para gestión de estado global
- `react-hook-form`: Para validación de formularios
- `react-toastify`: Para notificaciones toast
- `react-quill`: Para editor de texto enriquecido

### 2. Gestión de Estado

#### Store de Zustand (`lib/store.ts`)
Se creó un store global para gestionar:
- Estado de autenticación del usuario
- Información del usuario (incluyendo role)
- Funciones para login/logout
- Verificación de autenticación

#### Hooks Personalizados (`lib/hooks.ts`)
Se crearon hooks con SWR:
- `useMemos(status)`: Para obtener lista de memos filtrados por status
- `useMemoDetail(id)`: Para obtener detalle de un memo específico

### 3. Servicios

#### Servicio de Memos (`lib/memos.ts`)
Se implementó un servicio completo con métodos para:
- Obtener memos (con filtro por status)
- Crear, actualizar memos
- Enviar, aprobar, rechazar memos
- Subir adjuntos
- Crear respuestas

### 4. Componentes

#### LayoutProtected (`components/LayoutProtected.tsx`)
Componente HOC que:
- Verifica la autenticación del usuario
- Redirige a `/login` si no está autenticado
- Muestra el Sidebar y notificaciones toast

#### Sidebar (`components/Sidebar.tsx`)
Navegación lateral que:
- Muestra opciones según el rol del usuario
- SECONDARY_USER: Dashboard, Borradores, Enviados, Nuevo Memo
- DIRECTOR: Dashboard, Pendientes, Aprobados
- AREA_USER: Dashboard, Bandeja de Entrada

#### MemoForm (`components/MemoForm.tsx`)
Formulario completo para crear/editar memos con:
- Editor de texto enriquecido (ReactQuill)
- Selector de destinatarios (AREA_USER)
- Selector de aprobador (DIRECTOR)
- Subida de adjuntos PDF (solo en borradores)
- Validación con React Hook Form

### 5. Páginas

#### Dashboard (`app/dashboard/page.tsx`)
Página principal que muestra:
- Información del usuario
- Enlaces rápidos según el rol
- Tarjetas interactivas

#### Inbox (`app/dashboard/inbox/page.tsx`)
Lista de memos pendientes (DIRECTOR) o aprobados (AREA_USER)

#### Drafts (`app/dashboard/drafts/page.tsx`)
Lista de borradores y memos rechazados (SECONDARY_USER)

#### Sent (`app/dashboard/sent/page.tsx`)
Lista de memos enviados (SECONDARY_USER)

#### Approved (`app/dashboard/approved/page.tsx`)
Lista de memos aprobados (DIRECTOR)

#### Nuevo Memo (`app/memos/new/page.tsx`)
Página para crear un nuevo memo

#### Editar Memo (`app/memos/edit/[id]/page.tsx`)
Página para editar un memo existente (solo borradores)

#### Detalle Memo (`app/memos/[id]/page.tsx`)
Página completa que muestra:
- Información completa del memo
- Adjuntos
- PDF firmado (si está aprobado)
- Memo padre/hijos (si hay respuestas)
- Botones condicionales según rol y estado:
  - Editar (SECONDARY_USER, DRAFT)
  - Enviar a Aprobación (SECONDARY_USER, DRAFT)
  - Aprobar (DIRECTOR, PENDING_APPROVAL)
  - Rechazar (DIRECTOR, PENDING_APPROVAL)
  - Responder (cualquier usuario, APPROVED)

## Flujo Completo del Sistema

### Para SECONDARY_USER (Redactor):
1. Crear nuevo memo en `/memos/new`
2. Guardar como borrador
3. Editar borrador si es necesario
4. Subir adjuntos PDF
5. Enviar a aprobación
6. Si es rechazado, ver motivo y editar
7. Si es aprobado, ver en lista de enviados

### Para DIRECTOR (Aprobador):
1. Ver memos pendientes en `/dashboard/inbox`
2. Ver detalle del memo
3. Aprobar (genera PDF firmado automáticamente)
4. O rechazar (con motivo)
5. Ver memos aprobados en `/dashboard/approved`

### Para AREA_USER (Receptor):
1. Ver memos aprobados en `/dashboard/inbox`
2. Ver detalle del memo
3. Descargar PDF firmado
4. Responder al memo si es necesario

## Notificaciones

El sistema envía notificaciones por correo electrónico cuando:
- Un memo es enviado a aprobación (notifica al DIRECTOR)
- Un memo es aprobado (notifica a recipients y autor)
- Un memo es rechazado (notifica al autor con motivo)

En desarrollo, los emails se muestran en la consola del servidor Django.

## Archivos y Estructura

### Backend:
```
backend/
├── accounts/
│   ├── models.py (User con role)
│   ├── views.py (login, user profile, users list)
│   ├── serializers.py (UserSerializer con role)
│   └── urls.py
├── memos/
│   ├── models.py (Memo, MemoAttachment)
│   ├── permissions.py (permisos personalizados)
│   ├── serializers.py (serializers de memos)
│   ├── views.py (MemoViewSet)
│   ├── services.py (generación de PDF)
│   ├── signals.py (notificaciones)
│   ├── urls.py
│   └── admin.py
└── config/
    ├── settings.py (configuración)
    └── urls.py
```

### Frontend:
```
frontend/
├── app/
│   ├── dashboard/
│   │   ├── page.tsx
│   │   ├── inbox/page.tsx
│   │   ├── drafts/page.tsx
│   │   ├── sent/page.tsx
│   │   └── approved/page.tsx
│   ├── memos/
│   │   ├── new/page.tsx
│   │   ├── edit/[id]/page.tsx
│   │   └── [id]/page.tsx
│   └── login/page.tsx
├── components/
│   ├── LayoutProtected.tsx
│   ├── Sidebar.tsx
│   └── MemoForm.tsx
└── lib/
    ├── api.ts
    ├── auth.ts
    ├── store.ts
    ├── memos.ts
    └── hooks.ts
```

## Próximos Pasos

Para completar la implementación, se deben ejecutar:

1. **Migraciones de base de datos:**
   ```bash
   cd backend
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Instalar dependencias del frontend:**
   ```bash
   cd frontend
   npm install
   ```

3. **Crear usuarios de prueba con diferentes roles:**
   - Un usuario con rol SECONDARY_USER
   - Un usuario con rol DIRECTOR
   - Un usuario con rol AREA_USER

4. **Configurar imágenes de sello y firma (opcional):**
   - Colocar `seal.png` en `backend/media/seal.png`
   - Colocar `signature.png` en `backend/media/signature.png`

5. **Iniciar servidores:**
   - Backend: `python manage.py runserver`
   - Frontend: `npm run dev`

## Notas Técnicas

- El sistema utiliza JWT para autenticación
- Los permisos se validan tanto en el backend como en el frontend
- El PDF firmado se genera automáticamente al aprobar un memo
- Las notificaciones por email funcionan en desarrollo (consola) y producción (SMTP)
- El frontend usa SWR para caché y revalidación automática de datos
- Zustand maneja el estado global de autenticación
- React Hook Form valida los formularios
- ReactQuill proporciona un editor de texto enriquecido

## Verificación

Para verificar que todo funciona correctamente:

1. Iniciar sesión como SECONDARY_USER
2. Crear un nuevo memo
3. Subir un adjunto PDF
4. Enviar a aprobación
5. Iniciar sesión como DIRECTOR
6. Ver memo pendiente
7. Aprobar memo (verificar que se genera PDF)
8. Iniciar sesión como AREA_USER
9. Ver memo aprobado en bandeja de entrada
10. Ver PDF firmado
11. Responder al memo

Todos estos pasos deben funcionar sin errores.

