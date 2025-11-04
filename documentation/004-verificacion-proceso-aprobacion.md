# Verificación y Mejoras del Proceso de Aprobación

## Resumen de Cambios

Se ha verificado y mejorado el proceso completo de aprobación de memorándums, incluyendo la generación de PDF firmado, manejo de errores y notificaciones.

## Mejoras Implementadas

### 1. Backend - Endpoint de Aprobación (`memos/views.py`)

#### Validaciones Mejoradas
- Verificación de que el memo esté en estado `PENDING_APPROVAL`
- Verificación de que el usuario sea el aprobador asignado
- Manejo robusto de errores en la generación del PDF

#### Flujo de Aprobación
1. Validación de permisos y estado
2. Establecimiento de fecha de aprobación (`approved_at`)
3. Generación de PDF firmado con manejo de errores
4. Guardado del PDF en el campo `signed_file`
5. Cambio de estado a `APPROVED`
6. Disparo automático de signals para notificaciones

#### Manejo de Errores
- Si falla la generación del PDF, se registra el error pero el memo se aprueba igual
- Los errores se registran en los logs para debugging
- El proceso continúa incluso si hay problemas con adjuntos

### 2. Generación de PDF Firmado (`memos/services.py`)

#### Mejoras en `generate_signed_pdf`
- Escape de caracteres HTML especiales en el contenido del memo
- Manejo correcto de saltos de línea
- Mejora en el manejo de adjuntos PDF:
  - Verificación de existencia de archivos
  - Manejo de rutas relativas y absolutas
  - Logging de advertencias cuando los adjuntos no se pueden procesar
- Mejor manejo de errores con logging estructurado

#### Estructura del PDF Generado
1. Encabezado: "MEMORÁNDUM INTERNO"
2. Información del memo:
   - Asunto
   - Fecha de creación
   - Autor
   - Aprobador
   - Destinatarios
3. Contenido del memo (formateado)
4. Sello de la empresa (si existe `media/seal.png`)
5. Firma digitalizada (si existe `media/signature.png`)
6. Firma del aprobador con fecha
7. Adjuntos PDF concatenados (si existen)

### 3. Sistema de Notificaciones (`memos/signals.py`)

#### Mejoras Implementadas
- Uso de `pre_save` y `post_save` signals para detectar cambios reales de estado
- Cache del estado anterior para evitar notificaciones duplicadas
- Notificaciones solo cuando el estado realmente cambia:
  - `PENDING_APPROVAL`: Notifica al aprobador
  - `APPROVED`: Notifica a recipients y autor
  - `REJECTED`: Notifica al autor con motivo

#### Notificaciones por Email
- En desarrollo: Se muestran en la consola del servidor Django
- En producción: Se envían por SMTP configurado
- Manejo silencioso de errores (`fail_silently=True`) para no interrumpir el flujo

### 4. Frontend - Proceso de Aprobación

#### Validaciones en el Frontend
- Verificación de que el usuario sea DIRECTOR
- Verificación de que el memo esté en estado `PENDING_APPROVAL`
- Verificación de que el usuario sea el aprobador asignado
- Mensajes de error claros y específicos

#### Manejo de Respuestas
- Extracción correcta de mensajes de error de la API
- Notificaciones toast (o consola si no está instalado react-toastify)
- Actualización automática de la UI después de aprobar
- Redirección a la página de inbox después de aprobar

### 5. Mejoras en el Manejo de Adjuntos

#### Procesamiento de Adjuntos en PDF
- Verificación de existencia de archivos antes de procesar
- Manejo de diferentes formatos de rutas (absolutas, relativas)
- Logging de advertencias cuando un adjunto no se puede procesar
- Continuación del proceso aunque algunos adjuntos fallen

## Flujo Completo de Aprobación

### Paso a Paso

1. **SECONDARY_USER crea un memo:**
   - Estado inicial: `DRAFT`
   - Asigna aprobador (DIRECTOR)
   - Asigna destinatarios (AREA_USER)
   - Opcionalmente sube adjuntos PDF

2. **SECONDARY_USER envía a aprobación:**
   - Endpoint: `POST /api/memos/<id>/submit/`
   - Validaciones:
     - Memo en estado `DRAFT`
     - Usuario es el autor
     - Tiene aprobador asignado
     - Tiene al menos un destinatario
   - Cambio de estado: `DRAFT` → `PENDING_APPROVAL`
   - Signal notifica al aprobador por email

3. **DIRECTOR aprueba el memo:**
   - Endpoint: `POST /api/memos/<id>/approve/`
   - Validaciones:
     - Memo en estado `PENDING_APPROVAL`
     - Usuario es el aprobador asignado
   - Generación de PDF firmado:
     - Crea PDF con contenido del memo
     - Agrega sello y firma (si existen)
     - Concatena adjuntos PDF
     - Guarda en `signed_file`
   - Cambio de estado: `PENDING_APPROVAL` → `APPROVED`
   - Establece `approved_at`
   - Signal notifica a recipients y autor por email

4. **AREA_USER recibe el memo:**
   - Aparece en `/dashboard/inbox`
   - Puede ver el contenido
   - Puede descargar el PDF firmado
   - Puede responder al memo

## Validaciones y Seguridad

### Permisos
- Solo `DIRECTOR` puede aprobar memos
- Solo el aprobador asignado puede aprobar un memo específico
- Solo memos en `PENDING_APPROVAL` pueden ser aprobados

### Validaciones de Estado
- El memo debe tener un aprobador asignado antes de enviar
- El memo debe tener al menos un destinatario antes de enviar
- El estado se valida tanto en backend como en frontend

## Manejo de Errores

### Errores en Generación de PDF
- Si falla la generación, se registra el error
- El memo se aprueba igual (sin PDF firmado)
- El usuario recibe notificación de aprobación
- Los logs permiten identificar y corregir el problema

### Errores en Adjuntos
- Si un adjunto no es PDF, se omite con advertencia
- Si un adjunto no existe, se omite con advertencia
- El PDF principal se genera igual
- Los adjuntos válidos se concatenan correctamente

### Errores en Notificaciones
- Las notificaciones por email fallan silenciosamente
- No interrumpen el proceso de aprobación
- Los errores se registran en los logs

## Archivos Modificados

### Backend
- `backend/memos/views.py`: Mejoras en el endpoint de aprobación
- `backend/memos/services.py`: Mejoras en generación de PDF y manejo de adjuntos
- `backend/memos/signals.py`: Mejoras en detección de cambios de estado

### Frontend
- `frontend/app/memos/[id]/page.tsx`: Validaciones mejoradas y manejo de errores
- `frontend/lib/memos.ts`: Mejor extracción de mensajes de error

## Pruebas Recomendadas

1. **Crear memo y enviar a aprobación:**
   - Verificar que se requiere aprobador y destinatarios
   - Verificar que el estado cambia correctamente
   - Verificar notificación al aprobador

2. **Aprobar memo:**
   - Verificar generación de PDF firmado
   - Verificar que el estado cambia a APPROVED
   - Verificar que `approved_at` se establece
   - Verificar notificaciones a recipients y autor
   - Verificar que el PDF se puede descargar

3. **Manejo de errores:**
   - Probar con adjuntos inválidos
   - Probar sin imágenes de sello/firma
   - Verificar que el proceso continúa aunque falle el PDF

4. **Permisos:**
   - Intentar aprobar como usuario incorrecto
   - Intentar aprobar memo en estado incorrecto
   - Verificar mensajes de error apropiados

## Notas Técnicas

- El PDF se genera usando `reportlab` y `PyPDF2`
- Las imágenes de sello y firma son opcionales
- Los adjuntos se concatenan solo si son PDFs válidos
- Las notificaciones por email funcionan en desarrollo (consola) y producción (SMTP)
- El signal usa `pre_save` para detectar cambios reales de estado

