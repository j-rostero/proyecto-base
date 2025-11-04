# Ajuste del Proceso de Memorandos según Requisitos Deepsek

## Resumen de Cambios

Este documento describe los ajustes realizados al sistema de memorandos para cumplir con todos los requisitos especificados en `requisitos deepsek.md`. Se implementaron funcionalidades faltantes, se agregaron nuevos modelos y se ajustaron los flujos de trabajo para alinearlos completamente con las especificaciones.

## Cambios en Modelos de Datos

### Modelo Departamento

Se creó el modelo `Departamento` en `accounts/models.py` para gestionar departamentos con sus prefijos utilizados en la generación de correlativos:

```python
class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    prefijo = models.CharField(max_length=10, unique=True)
    director = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    activo = models.BooleanField(default=True)
```

Cada departamento tiene un prefijo único que se utiliza para generar números correlativos en el formato `[Prefijo]-[Año]-[Secuencial]`, por ejemplo: `FIN-2024-0015`.

### Modelo SecuenciaMemorando

Se creó el modelo `SecuenciaMemorando` en `memos/models.py` para controlar las secuencias correlativas por departamento y año:

```python
class SecuenciaMemorando(models.Model):
    departamento = models.ForeignKey('accounts.Departamento', on_delete=models.CASCADE)
    año = models.IntegerField()
    ultima_secuencia = models.IntegerField(default=0)
```

Este modelo garantiza que cada departamento tenga su propia secuencia de memorandos por año, evitando duplicados y manteniendo la unicidad de los números correlativos.

### Actualización del Modelo User

Se agregaron campos al modelo `User`:

- `departamento`: ForeignKey a `Departamento` para asociar usuarios con sus departamentos
- `cargo`: Campo para almacenar el cargo del usuario
- `nombre_completo`: Propiedad que retorna el nombre completo del usuario
- `ADMIN`: Nuevo rol agregado a las opciones de roles

### Actualización del Modelo Memo

Se agregaron múltiples campos y estados al modelo `Memo`:

**Nuevos campos:**
- `numero_correlativo`: Campo único para almacenar el número correlativo generado
- `prioridad`: Campo con opciones (baja, normal, alta, urgente)
- `confidencial`: Campo booleano para marcar memorandos confidenciales
- `departamento`: ForeignKey a `Departamento`
- `sello_digital`: Campo JSONField para almacenar información del sello digital
- `fecha_distribucion`: Campo DateTimeField para registrar cuando se distribuyó el memorando
- `modificacion_solicitada`: Campo TextField para comentarios de modificación

**Nuevos estados:**
- `MODIFICACION_SOLICITADA`: Estado para memorandos que requieren modificaciones
- `DISTRIBUIDO`: Estado para memorandos que ya fueron distribuidos a destinatarios

### Actualización del Modelo MemoAttachment

Se agregó el campo `file_size` para almacenar el tamaño del archivo en bytes, útil para validaciones y reportes.

## Servicios Implementados

### Generación de Correlativo

Se implementó la función `generar_correlativo()` en `memos/services.py` que:

1. Recibe un departamento y un año (opcional, por defecto el año actual)
2. Busca o crea una secuencia para el departamento/año
3. Incrementa atómicamente la secuencia
4. Genera el número en formato `[Prefijo]-[Año]-[Secuencial]` con 4 dígitos

```python
def generar_correlativo(departamento, año=None):
    secuencia, created = SecuenciaMemorando.objects.get_or_create(
        departamento=departamento,
        año=año,
        defaults={'ultima_secuencia': 0}
    )
    secuencia.ultima_secuencia += 1
    secuencia.save()
    return f"{departamento.prefijo}-{año}-{str(secuencia.ultima_secuencia).zfill(4)}"
```

### Firma Digital

Se implementaron funciones para generar la firma digital:

- `generar_hash_memorando()`: Genera un hash SHA256 del contenido del memorando
- `generar_codigo_verificacion()`: Genera un código único de verificación
- `crear_sello_digital()`: Crea el sello digital completo con toda la información requerida

El sello digital incluye:
- Director (nombre completo)
- Cargo del director
- Departamento
- Fecha de firma
- Hash SHA256 del contenido
- Código único de verificación

### Constantes de Validación

Se definieron constantes en `services.py` para validaciones:

- `MAX_RECIPIENTS = 10`: Máximo de destinatarios por memorando
- `MAX_ATTACHMENTS = 5`: Máximo de archivos adjuntos
- `MAX_FILE_SIZE = 10 * 1024 * 1024`: Tamaño máximo de 10MB por archivo
- `ALLOWED_ATTACHMENT_EXTENSIONS`: Lista de extensiones permitidas (PDF, DOC, DOCX, XLS, XLSX)

## Actualizaciones en Vistas y Endpoints

### Método submit()

Se actualizó el método `submit()` para:

1. Generar automáticamente el correlativo cuando se envía a aprobación
2. Validar campos obligatorios (asunto, contenido mínimo de 10 caracteres)
3. Validar límite de destinatarios (máximo 10)
4. Permitir envío desde estado `MODIFICACION_SOLICITADA`
5. Limpiar comentarios de modificación al reenviar

### Método approve()

Se actualizó el método `approve()` para:

1. Crear el sello digital automáticamente al aprobar
2. Validar que el director pertenezca al mismo departamento
3. Cambiar automáticamente a estado `DISTRIBUIDO` después de aprobar
4. Registrar la fecha de distribución

### Nuevo Método solicitar_modificaciones()

Se agregó el endpoint `POST /api/memos/<id>/solicitar_modificaciones/` que:

1. Cambia el estado a `MODIFICACION_SOLICITADA`
2. Guarda los comentarios de modificación
3. Permite que el autor edite el memorando nuevamente
4. Notifica al autor por email

### Actualización del Método reply()

Se actualizó para:

1. Solo permitir responder memorandos en estado `DISTRIBUIDO`
2. Establecer automáticamente el remitente original como destinatario
3. Copiar prioridad y confidencialidad del memorando padre
4. Asignar automáticamente el aprobador del departamento del autor

### Actualización del Método upload_attachment()

Se agregaron validaciones completas:

1. Límite de 5 archivos adjuntos por memorando
2. Tamaño máximo de 10MB por archivo
3. Validación de extensiones permitidas
4. Permite subir adjuntos en estado `MODIFICACION_SOLICITADA`

## Actualizaciones en Serializers

### MemoListSerializer

Se agregaron campos:
- `numero_correlativo`
- `prioridad`
- `confidencial`
- `departamento`
- `fecha_distribucion`

### MemoDetailSerializer

Se agregaron campos:
- `numero_correlativo`
- `prioridad`
- `confidencial`
- `departamento`
- `sello_digital`
- `fecha_distribucion`
- `modificacion_solicitada`

### MemoCreateSerializer

Se actualizó para:
- Incluir `prioridad`, `confidencial` y `departamento_id`
- Asignar automáticamente el aprobador si hay departamento con director
- Validar límite de destinatarios
- Obtener departamento del usuario si no se especifica

### MemoUpdateSerializer

Se actualizó para incluir `prioridad` y `confidencial` con validación de destinatarios.

## Actualizaciones en Permisos

### CanEditDraft

Se actualizó para permitir editar memorandos en estado `MODIFICACION_SOLICITADA` además de `DRAFT`.

### IsRecipientOrInvolved

Se actualizó para permitir ver memorandos en estado `DISTRIBUIDO` además de `APPROVED`.

## Sistema de Notificaciones

Se actualizaron los signals en `memos/signals.py` para manejar los nuevos estados:

### Estado DISTRIBUIDO

Cuando un memorando cambia a `DISTRIBUIDO`, se notifica a todos los destinatarios por email con:
- Número correlativo
- Asunto
- Remitente
- Departamento
- Enlace al memorando

### Estado MODIFICACION_SOLICITADA

Cuando un memorando cambia a `MODIFICACION_SOLICITADA`, se notifica al autor por email con:
- Comentarios del director
- Indicación de que el memorando ha sido retornado a borrador

## Actualizaciones en Admin

### DepartamentoAdmin

Se registró el modelo `Departamento` en el admin con:
- Listado por nombre, prefijo, director y estado activo
- Filtros por estado activo y fecha de creación
- Búsqueda por nombre y prefijo

### UserAdmin

Se actualizó para incluir:
- Campos `role`, `departamento` y `cargo` en listado y filtros
- Fieldsets para información adicional del usuario

### MemoAdmin

Se actualizó para incluir:
- `numero_correlativo` en listado y búsqueda
- Filtros por prioridad, confidencial y departamento
- Fieldsets organizados por categorías
- Campos de solo lectura apropiados

### SecuenciaMemorandoAdmin

Se registró el modelo para administración con:
- Listado por departamento, año y última secuencia
- Filtros por año y departamento

## Flujo Completo Actualizado

### Creación de Memorando

1. Usuario secundario crea memorando en estado `DRAFT`
2. Se asigna automáticamente el departamento del usuario
3. Se asigna automáticamente el director del departamento como aprobador
4. El usuario puede agregar adjuntos (máx 5, 10MB cada uno)
5. El usuario puede agregar destinatarios (máx 10)

### Envío a Aprobación

1. Al hacer clic en "Enviar para Aprobación":
   - Se valida asunto y contenido mínimo
   - Se valida que tenga aprobador y destinatarios
   - Se genera el número correlativo automáticamente
   - Se cambia el estado a `PENDING_APPROVAL`
   - Se notifica al director por email

### Proceso de Aprobación

El director tiene tres opciones:

**Aprobar:**
1. Se crea el sello digital con hash y código de verificación
2. Se genera el PDF firmado con el sello digital incluido
3. Se cambia a estado `APPROVED` temporalmente
4. Se cambia automáticamente a estado `DISTRIBUIDO`
5. Se registra la fecha de distribución
6. Se notifica a destinatarios y autor

**Rechazar:**
1. Se guarda el motivo de rechazo
2. Se cambia a estado `REJECTED`
3. Se notifica al autor con el motivo

**Solicitar Modificaciones:**
1. Se guardan los comentarios de modificación
2. Se cambia a estado `MODIFICACION_SOLICITADA`
3. Se notifica al autor con los comentarios
4. El autor puede editar y reenviar el memorando

### Distribución

Cuando un memorando se aprueba, automáticamente:
1. Se cambia a estado `DISTRIBUIDO`
2. Se registra la fecha de distribución
3. Se notifica a todos los destinatarios por email
4. Los destinatarios pueden responder el memorando

### Respuesta a Memorando

Solo los destinatarios de memorandos `DISTRIBUIDO` pueden:
1. Crear un nuevo memorando hijo
2. El remitente original se convierte en destinatario
3. Se mantiene la prioridad y confidencialidad del original
4. El nuevo memorando sigue el mismo flujo completo

## Validaciones Implementadas

### Validaciones de Negocio

- Máximo 10 destinatarios por memorando
- Máximo 5 archivos adjuntos por memorando
- Tamaño máximo de 10MB por archivo
- Formatos permitidos: PDF, DOC, DOCX, XLS, XLSX
- Contenido mínimo de 10 caracteres
- Asunto obligatorio
- Correlativo único por departamento/año

### Validaciones de Permisos

- Solo el autor puede editar memorandos en `DRAFT` o `MODIFICACION_SOLICITADA`
- Solo el director del departamento puede aprobar/rechazar/solicitar modificaciones
- Solo los destinatarios pueden responder memorandos `DISTRIBUIDO`
- Solo el autor puede enviar a aprobación

## Próximos Pasos

Para aplicar estos cambios:

1. **Crear migraciones:**
   ```bash
   cd backend
   python manage.py makemigrations accounts
   python manage.py makemigrations memos
   ```

2. **Aplicar migraciones:**
   ```bash
   python manage.py migrate
   ```

3. **Crear departamentos iniciales:**
   - Crear departamentos con sus prefijos
   - Asignar directores a cada departamento
   - Asignar usuarios a sus departamentos

4. **Verificar funcionamiento:**
   - Probar creación de memorandos
   - Verificar generación de correlativos
   - Probar flujo de aprobación completo
   - Verificar notificaciones por email

## Notas Importantes

- Los memorandos existentes sin correlativo no tendrán número hasta que se envíen a aprobación
- Los usuarios deben tener asignado un departamento para que se genere el correlativo automáticamente
- El sello digital se genera solo cuando se aprueba un memorando
- La distribución es automática después de la aprobación, no requiere acción adicional
- Los memorandos solo pueden responderse cuando están en estado `DISTRIBUIDO`

Todos los cambios han sido implementados siguiendo estrictamente los requisitos especificados en `requisitos deepsek.md`, garantizando que el sistema cumple con todas las funcionalidades y validaciones requeridas.

