**Objetivo del Proyecto:**
Desarrollar una aplicación web full-stack para la digitalización y gestión del flujo de memorándums internos. El sistema debe gestionar roles, un ciclo de vida de aprobación (borrador, aprobación, firma) y la distribución final, utilizando **Django Rest Framework (DRF)** para el backend y **Next.js** para el frontend.

---

###  Backend (Django Rest Framework)

#### 1. Modelos de Datos (models.py)

**a. Usuario y Roles:**
* Extender el `AbstractUser` de Django.
* Añadir un campo `role` con opciones (Choices): `SECONDARY_USER` (Redactor), `DIRECTOR` (Aprobador), `AREA_USER` (Receptor).

**b. Modelo `Memo`:**
* `subject` (CharField): Asunto del memo.
* `body` (TextField): Contenido principal.
* `status` (CharField): Estado del memo (Choices: `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`).
* `author` (ForeignKey al `User`, `related_name='authored_memos'`): El `SECONDARY_USER` que lo crea.
* `approver` (ForeignKey al `User`, `related_name='approved_memos'`, nullable=True): El `DIRECTOR` que aprueba.
* `recipients` (ManyToManyField al `User`, `related_name='received_memos'`): Los `AREA_USER` destinatarios.
* `created_at` (DateTimeField, auto_now_add=True).
* `approved_at` (DateTimeField, nullable=True): Fecha de aprobación.
* `parent_memo` (ForeignKey a 'self', on_delete=SET_NULL, nullable=True, related_name='replies'): Para el "memo hijo".
* `signed_file` (FileField, upload_to='signed_memos/', nullable=True): El PDF final sellado.

**c. Modelo `MemoAttachment`:**
* `memo` (ForeignKey al `Memo`, related_name='attachments').
* `file` (FileField, upload_to='memo_attachments/'): Los PDF adjuntos en estado de borrador.
* `uploaded_by` (ForeignKey al `User`).

#### 2. Lógica de Negocio y Serializers (serializers.py / views.py)

**a. Autenticación y Roles (Simple JWT):**
* Implementar autenticación basada en tokens JWT.
* Proteger todos los endpoints.
* Crear permisos personalizados (Custom Permissions) para DRF:
    * `IsSecondaryUser`: Solo puede crear/editar `DRAFT`.
    * `IsDirector`: Solo puede cambiar estado de `PENDING_APPROVAL` a `APPROVED`/`REJECTED`.
    * `IsRecipientOrInvolved`: Puede ver memos `APPROVED` donde es `recipient` o `author`.

**b. Endpoints de API (views.py / urls.py):**

* **Autenticación:**
    * `POST /api/auth/login/` (TokenObtainPairView)
    * `GET /api/auth/user/` (Devuelve el `user` y su `role`).

* **Gestión de Memos (ModelViewSet para `Memo`):**
    * `GET /api/memos/`: Listar memos.
        * *QueryParam `status=DRAFT`*: Devuelve los borradores del `author` logueado.
        * *QueryParam `status=PENDING_APPROVAL`*: Devuelve memos pendientes al `DIRECTOR`.
        * *QueryParam `status=APPROVED`*: Devuelve memos aprobados a los `recipients`.
    * `POST /api/memos/`: Crear nuevo memo. Solo `author`. Estado inicial: `DRAFT`.
    * `PATCH /api/memos/<id>/`: Actualizar memo (solo si `status=DRAFT`).
    * `GET /api/memos/<id>/`: Ver detalle de un memo.

* **Gestión de Adjuntos (dentro de Memos):**
    * `POST /api/memos/<id>/attachments/`: Subir un PDF adjunto. Solo permitido si el memo está en `DRAFT`.

* **Acciones de Flujo (Endpoints de Acción con `@action`):**
    * `POST /api/memos/<id>/submit/` (Acción del `SECONDARY_USER`):
        * Cambia `status` de `DRAFT` a `PENDING_APPROVAL`.
        * Notifica al `DIRECTOR` asignado.
    * `POST /api/memos/<id>/approve/` (Acción del `DIRECTOR`):
        * **Lógica de Firma/Sello:**
            1.  Generar un PDF "final" (usando `reportlab` o `PyPDF2`).
            2.  Este PDF debe incluir: `subject`, `body`, y una imagen del "Sello de la Empresa" y la "Firma Digitalizada" del director.
            3.  Concatenar los `MemoAttachment` (PDFs originales) a este PDF generado.
            4.  Guardar este PDF final en el campo `signed_file` del `Memo`.
        * Cambia `status` a `APPROVED`.
        * Establece `approved_at` a `now()`.
        * Dispara la **notificación** a todos los `recipients`.
    * `POST /api/memos/<id>/reject/` (Acción del `DIRECTOR`):
        * Cambia `status` a `REJECTED`.
        * (Opcional: Requerir un campo `rejection_reason`).
    * `POST /api/memos/<id>/reply/` (Acción de `RECIPIENT` o `DIRECTOR`):
        * Crea un nuevo memo (en `DRAFT`) y asigna el `id` actual a `parent_memo` del nuevo.

**c. Notificaciones:**
* Utilizar **Django Signals** (`post_save` en `Memo`).
* Cuando `status` cambia a `APPROVED` o `REJECTED`, enviar un correo (o notificación push) a los usuarios correspondientes.

---

### Frontend (Next.js)

#### 1. Estructura de Páginas (App Router o Pages Router)

* `/login`: Página de inicio de sesión (usa `axios` o `fetch` para `api/auth/login/`). Gestión del JWT (guardar en `localStorage` o `cookies`).
* `/dashboard`: Página principal (Layout Protegido / Ruta Privada).
* `/dashboard/inbox`: (Para `DIRECTOR` y `AREA_USER`). Lista de memos `PENDING_APPROVAL` (si es Director) o `APPROVED` (si es Receptor).
* `/dashboard/drafts`: (Para `SECONDARY_USER`). Lista de memos con `status=DRAFT` o `REJECTED`.
* `/dashboard/sent`: (Para `SECONDARY_USER`). Memos enviados (`PENDING_APPROVAL` o `APPROVED`).

#### 2. Componentes Clave

* **`LayoutProtected` (Higher-Order Component):**
    * Verifica la existencia del JWT.
    * Obtiene `api/auth/user/` para verificar el rol.
    * Redirige a `/login` si no está autenticado.
    * Muestra la navegación (Sidebar) según el rol del usuario.

* **`MemoForm` (Página `/memos/new` y `/memos/edit/<id>`):**
    * Formulario con campos: `subject`, `body` (usar un editor de texto enriquecido como `ReactQuill`).
    * Selector de `recipients` (lista de `AREA_USER`).
    * Selector de `approver` (lista de `DIRECTOR`).
    * Componente `FileUpload` para subir PDFs (POST a `api/memos/<id>/attachments/`).
    * Botón "Guardar Borrador" (`PATCH`).
    * Botón "Enviar a Aprobación" (POST a `api/memos/<id>/submit/`).

* **`MemoDetail` (Página `/memos/<id>`):**
    * Renderiza el contenido del memo.
    * Muestra los adjuntos (`MemoAttachment`).
    * Muestra el PDF final firmado (`signed_file`) si está `APPROVED`.
    * Muestra el historial (Borrador -> Pendiente -> Aprobado).
    * Muestra el "Memo Padre" o "Memo Hijo" (links a otros memos).
    * **Lógica Condicional de Botones (Según Rol):**
        * Si `DIRECTOR` y `status=PENDING_APPROVAL`: Mostrar botones "Aprobar" y "Rechazar".
        * Si `status=APPROVED`: Mostrar botón "Responder" (POST a `api/memos/<id>/reply/`).

#### 3. Gestión de Estado y Datos (Client-Side)

* **Gestión de Estado Global:** Utilizar **Zustand** (preferido por su simplicidad) o **React Context API** para gestionar el estado de autenticación del usuario (token, `user.role`, `isAuthenticated`).
* **Fetching de Datos (SWR o React Query):**
    * Implementar SWR (preferido por Vercel/Next.js) o React Query para el *caching*, *revalidación* y *mutación* de los datos de la API de DRF.
    * Crear *hooks* personalizados (ej. `useMemos(status)`, `useMemoDetail(id)`) que encapsulen la lógica de SWR y el *fetching* con `axios`.
    * Usar `mutate` de SWR para actualizar automáticamente la UI después de una acción (ej. al aprobar un memo, `mutate` el *hook* `useMemos('PENDING_APPROVAL')` y `useMemos('APPROVED')`).
* **Gestión de Formularios:** Usar **React Hook Form** para la validación de formularios (creación/edición de memos).

#### 4. Notificaciones (UI)

* Utilizar una librería como **`react-toastify`** o **`sonner`** para mostrar notificaciones *toast* no intrusivas en la UI cuando:
    * Se envía un memo (`"Memo enviado a aprobación"`).
    * Se aprueba un memo (`"Memo aprobado y distribuido"`).
    * Ocurre un error en la API (`"Error: No se pudo cargar el adjunto"`).






