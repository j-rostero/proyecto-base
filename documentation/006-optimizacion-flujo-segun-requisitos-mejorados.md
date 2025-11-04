# Optimización del Flujo de Gestión de Memorandos según Requisitos Mejorados

## Resumen de Cambios

Este documento describe las optimizaciones implementadas en el sistema de gestión de memorandos según los requisitos mejorados especificados en `requisitos deepsek mejorada.md`. Se implementaron mejoras significativas en el sistema correlativo, la firma digital, la distribución, las validaciones y el sistema de respuestas.

## 1. Sistema Correlativo Mejorado por Departamento

### 1.1. Formato Mejorado con Mes

Se actualizó el formato del número correlativo para incluir el mes en la estructura:

**Formato anterior:** `[Prefijo]-[Año]-[Secuencial]`  
**Formato mejorado:** `[Prefijo]-[Año]-[Mes]-[Secuencial]`

**Ejemplo:** `FIN-2024-03-0042`

### 1.2. Actualización del Modelo SecuenciaMemorando

Se modificó el modelo `SecuenciaMemorando` en `backend/memos/models.py` para incluir el campo `mes` y campos adicionales:

```python
class SecuenciaMemorando(models.Model):
    departamento = models.ForeignKey('accounts.Departamento', ...)
    año = models.IntegerField(verbose_name='Año', validators=[MaxValueValidator(9999)])
    mes = models.IntegerField(
        verbose_name='Mes',
        validators=[MaxValueValidator(12), models.MinValueValidator(1)],
        help_text='Mes (1-12)'
    )
    ultima_secuencia = models.IntegerField(default=0)
    prefijo = models.CharField(max_length=10, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['departamento', 'año', 'mes']]
        indexes = [
            models.Index(fields=['departamento', 'año', 'mes']),
        ]
```

### 1.3. Algoritmo de Generación con Bloqueo Transaccional

Se mejoró la función `generar_correlativo` en `backend/memos/services.py` para utilizar transacciones con bloqueo SELECT FOR UPDATE, evitando condiciones de carrera en entornos concurrentes:

```python
def generar_correlativo(departamento, año=None, mes=None):
    """
    Genera un número correlativo único con formato mejorado.
    Utiliza transacciones con bloqueo para evitar duplicados concurrentes.
    """
    from django.db import transaction
    
    ahora = datetime.now()
    if año is None:
        año = ahora.year
    if mes is None:
        mes = ahora.month
    
    prefijo = departamento.prefijo
    
    # Usar transacción con bloqueo SELECT FOR UPDATE
    with transaction.atomic():
        secuencia = SecuenciaMemorando.objects.select_for_update().filter(
            departamento=departamento,
            año=año,
            mes=mes
        ).first()
        
        if secuencia:
            secuencia.ultima_secuencia += 1
            secuencia.actualizado_en = timezone.now()
            secuencia.save(update_fields=['ultima_secuencia', 'actualizado_en', 'prefijo'])
        else:
            secuencia = SecuenciaMemorando.objects.create(
                departamento=departamento,
                año=año,
                mes=mes,
                ultima_secuencia=1,
                prefijo=prefijo
            )
    
    # Formatear con el formato mejorado
    secuencial_formateado = str(secuencia.ultima_secuencia).zfill(4)
    mes_formateado = str(mes).zfill(2)
    correlativo = f"{prefijo}-{año}-{mes_formateado}-{secuencial_formateado}"
    
    return correlativo
```

Este enfoque garantiza que no se generen números correlativos duplicados incluso en entornos de alta concurrencia.

## 2. Firma Digital Avanzada con Metadatos Completos

### 2.1. Estructura del Sello Digital Mejorado

Se actualizó la función `crear_sello_digital` para incluir metadatos avanzados según los requisitos mejorados:

```python
def crear_sello_digital(memo, request=None):
    """
    Crea el sello digital avanzado con metadatos completos.
    Incluye información del director, timestamp, hash, código de verificación
    y metadatos de seguridad (IP, user agent, ubicación aproximada).
    """
    director = memo.approver
    departamento = memo.departamento
    
    # Obtener metadatos del request
    metadatos = {}
    if request:
        metadatos = {
            'ip': obtener_ip_cliente(request),
            'userAgent': request.META.get('HTTP_USER_AGENT', 'N/A'),
            'ubicacion': obtener_ubicacion_aproximada(request)
        }
    
    sello = {
        'version': '1.0',
        'director': {
            'id': director.id,
            'nombre': director.nombre_completo or director.username,
            'cargo': director.cargo or 'Director',
            'departamento': departamento.nombre if departamento else 'N/A'
        },
        'timestamp': timezone.now().isoformat(),
        'hashDocumento': generar_hash_memorando(memo),
        'codigoVerificacion': generar_codigo_verificacion(),
        'metadatos': metadatos
    }
    
    return sello
```

### 2.2. Funciones Auxiliares para Metadatos

Se implementaron funciones para capturar información de seguridad:

```python
def obtener_ip_cliente(request):
    """Obtiene la IP real del cliente desde el request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'N/A')
    return ip

def obtener_ubicacion_aproximada(request):
    """Obtiene ubicación aproximada basada en IP."""
    ip = obtener_ip_cliente(request)
    return {
        'ip': ip,
        'nota': 'Ubicación aproximada basada en IP (requiere servicio externo)'
    }
```

### 2.3. Código de Verificación Mejorado

Se aumentó la longitud del código de verificación de 16 a 32 caracteres para mayor seguridad:

```python
def generar_codigo_verificacion():
    """Genera un código único de verificación URL-safe de 32 caracteres."""
    return secrets.token_urlsafe(32)
```

## 3. Sistema de Distribución Mejorado

### 3.1. Modelo DistribucionMemorando

Se creó un nuevo modelo para registrar cada distribución individual a destinatarios:

```python
class DistribucionMemorando(models.Model):
    class EstadoDistribucion(models.TextChoices):
        ENVIADO = 'ENVIADO', 'Enviado'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        ERROR = 'ERROR', 'Error'
        PENDIENTE = 'PENDIENTE', 'Pendiente'
    
    class MetodoDistribucion(models.TextChoices):
        SISTEMA = 'SISTEMA', 'Sistema'
        EMAIL = 'EMAIL', 'Email'
        PUSH = 'PUSH', 'Notificación Push'
    
    memorandum = models.ForeignKey(Memo, on_delete=models.CASCADE, related_name='distribuciones')
    destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tipo_destinatario = models.CharField(max_length=20, default='PRINCIPAL')
    fecha_envio = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    metodo = models.CharField(max_length=20, choices=MetodoDistribucion.choices, default='SISTEMA')
    estado = models.CharField(max_length=20, choices=EstadoDistribucion.choices, default='ENVIADO')
    error = models.TextField(null=True, blank=True)
    acuse_recibo = models.BooleanField(default=False)
    fecha_acuse = models.DateTimeField(null=True, blank=True)
```

Este modelo permite rastrear el estado de cada distribución individual, facilitando el seguimiento y la resolución de problemas.

### 3.2. Función de Distribución Mejorada

Se implementó la función `distribuir_memorando` que crea registros de distribución y maneja errores de forma individual:

```python
def distribuir_memorando(memorando_id, request=None):
    """
    Distribuye un memorando aprobado a todos sus destinatarios.
    Crea registros de distribución y envía notificaciones.
    """
    memorando = Memo.objects.get(id=memorando_id)
    resultados = []
    
    with transaction.atomic():
        for destinatario in memorando.recipients.all():
            try:
                # Crear registro de distribución
                distribucion = DistribucionMemorando.objects.create(
                    memorandum=memorando,
                    destinatario=destinatario,
                    tipo_destinatario='PRINCIPAL',
                    metodo=DistribucionMemorando.MetodoDistribucion.SISTEMA,
                    estado=DistribucionMemorando.EstadoDistribucion.ENVIADO
                )
                
                # Enviar notificación por email
                if destinatario.email:
                    try:
                        send_mail(...)
                        distribucion.estado = DistribucionMemorando.EstadoDistribucion.ENTREGADO
                        distribucion.fecha_entrega = timezone.now()
                        distribucion.save()
                    except Exception as e:
                        distribucion.estado = DistribucionMemorando.EstadoDistribucion.ERROR
                        distribucion.error = str(e)
                        distribucion.save()
                
                resultados.append({
                    'destinatario': destinatario.nombre_completo,
                    'estado': distribucion.estado,
                    'distribucionId': distribucion.id
                })
            except Exception as error:
                resultados.append({
                    'destinatario': destinatario.nombre_completo,
                    'estado': 'ERROR',
                    'error': str(error)
                })
        
        # Actualizar estado general del memorando
        memorando.status = Memo.Status.DISTRIBUIDO
        memorando.fecha_distribucion = timezone.now()
        memorando.save()
    
    return resultados
```

Esta implementación permite que si un destinatario falla, los demás continúan recibiendo el memorando, mejorando la robustez del sistema.

## 4. Validaciones y Reglas de Negocio Mejoradas

### 4.1. Límites del Sistema Actualizados

Se actualizaron las constantes de validación según los requisitos mejorados:

```python
# Constantes de validación mejoradas
MAX_RECIPIENTS = 15  # Actualizado de 10 a 15
MAX_ATTACHMENTS = 5
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TOTAL_SIZE = 25 * 1024 * 1024  # 25MB total
MAX_BORRADORES_SIMULTANEOS = 50
TIEMPO_MAXIMO_BORRADOR = 30  # días
TIEMPO_MAXIMO_APROBACION = 72  # horas
MAX_PROFUNDIDAD_HILO = 10
MAX_RESPUESTAS_POR_MEMO = 20
TIEMPO_MAXIMO_RESPUESTA = 90  # días
```

### 4.2. Validaciones en el Proceso de Aprobación

Se mejoraron las validaciones en el método `approve` para incluir el request y pasar metadatos al sello digital:

```python
@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDirector])
def approve(self, request, pk=None):
    # ... validaciones existentes ...
    
    # Crear sello digital avanzado con metadatos
    memo.sello_digital = crear_sello_digital(memo, request)
    
    # ... generación de PDF ...
    
    # Distribuir automáticamente usando el sistema mejorado
    resultados_distribucion = distribuir_memorando(memo.id, request)
```

## 5. Sistema de Respuestas Mejorado

### 5.1. Validaciones Avanzadas en Respuestas

Se implementaron validaciones completas para el sistema de respuestas:

```python
@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
def reply(self, request, pk=None):
    """
    Crear un nuevo memo como respuesta mejorada con validaciones avanzadas.
    """
    parent_memo = self.get_object()
    
    # Validar tiempo máximo de respuesta (90 días)
    if parent_memo.fecha_distribucion:
        tiempo_transcurrido = timezone.now() - parent_memo.fecha_distribucion
        if tiempo_transcurrido.days > TIEMPO_MAXIMO_RESPUESTA:
            return Response({'error': 'Tiempo máximo expirado'}, ...)
    
    # Validar profundidad del hilo
    profundidad = calcular_profundidad_hilo(parent_memo)
    if profundidad >= MAX_PROFUNDIDAD_HILO:
        return Response({'error': 'Profundidad máxima alcanzada'}, ...)
    
    # Validar número máximo de respuestas
    total_respuestas = contar_respuestas_memo(parent_memo)
    if total_respuestas >= MAX_RESPUESTAS_POR_MEMO:
        return Response({'error': 'Máximo de respuestas alcanzado'}, ...)
    
    # Verificar si ya existe una respuesta del usuario
    respuesta_existente = Memo.objects.filter(
        parent_memo=parent_memo,
        author=request.user
    ).exists()
    
    if respuesta_existente:
        return Response({'error': 'Ya ha respondido a este memorando'}, ...)
```

### 5.2. Funciones Auxiliares para Respuestas

Se crearon funciones auxiliares para manejar la lógica de respuestas:

```python
def calcular_profundidad_hilo(memo):
    """Calcula la profundidad del hilo de conversación."""
    profundidad = 0
    memo_actual = memo
    while memo_actual.parent_memo:
        profundidad += 1
        memo_actual = memo_actual.parent_memo
        if profundidad > 100:  # Protección contra bucles infinitos
            break
    return profundidad

def contar_respuestas_memo(memo):
    """Cuenta todas las respuestas directas e indirectas de un memo."""
    def contar_recursivo(m):
        count = m.replies.count()
        for reply in m.replies.all():
            count += contar_recursivo(reply)
        return count
    return contar_recursivo(memo)

def generar_contenido_respuesta(memo_padre):
    """Genera contenido de respuesta con contexto del memorando original."""
    contenido = f"""
--- Respuesta al memorando {memo_padre.numero_correlativo or 'N/A'} ---

Asunto original: {memo_padre.subject}
Fecha: {memo_padre.fecha_distribucion.strftime('%d/%m/%Y') if memo_padre.fecha_distribucion else 'N/A'}

---
Respuesta:
"""
    return contenido.strip()
```

### 5.3. Manejo de Contexto en Respuestas

Se mejoró la creación de respuestas para incluir opciones de incluir todos los destinatarios:

```python
# Establecer destinatario como el remitente original más otros opcionales
new_recipients = [parent_memo.author]
incluir_todos = request.data.get('incluir_todos_destinatarios', False)

if incluir_todos:
    # Incluir todos los destinatarios del original excepto el que responde
    for dest in parent_memo.recipients.all():
        if dest.id != request.user.id and dest not in new_recipients:
            new_recipients.append(dest)
```

## 6. Cambios en las Vistas

### 6.1. Actualización del Método Approve

Se actualizó el método `approve` para usar el sistema de distribución mejorado:

```python
# Distribuir automáticamente usando el sistema mejorado
try:
    from .services import distribuir_memorando
    resultados_distribucion = distribuir_memorando(memo.id, request)
    logger.info(f"Memorando {memo.id} distribuido: {resultados_distribucion}")
except Exception as e:
    logger.error(f'Error al distribuir memorando {memo.id}: {str(e)}')
```

### 6.2. Actualización del Método Submit

El método `submit` ahora utiliza el formato mejorado de correlativo automáticamente:

```python
# Generar correlativo si no existe (formato mejorado con mes)
if not memo.numero_correlativo and memo.departamento:
    memo.numero_correlativo = generar_correlativo(memo.departamento)
```

## 7. Migraciones Necesarias

Para aplicar estos cambios, se requiere crear una migración que:

1. Agregue el campo `mes` al modelo `SecuenciaMemorando`
2. Agregue los campos `prefijo`, `creado_en`, `actualizado_en` a `SecuenciaMemorando`
3. Actualice el `unique_together` para incluir `mes`
4. Cree el modelo `DistribucionMemorando`

**Comando para crear la migración:**
```bash
python manage.py makemigrations memos
python manage.py migrate
```

## 8. Beneficios de las Optimizaciones

### 8.1. Sistema Correlativo
- **Trazabilidad mejorada:** El formato con mes facilita la organización y búsqueda de memorandos
- **Concurrencia segura:** El bloqueo transaccional previene duplicados en entornos concurrentes
- **Mejor rendimiento:** Los índices optimizados mejoran las consultas

### 8.2. Firma Digital
- **Mayor seguridad:** Metadatos completos permiten auditoría detallada
- **Trazabilidad de origen:** IP y user agent registran el origen de la firma
- **Código de verificación robusto:** Tokens de 32 caracteres aumentan la seguridad

### 8.3. Distribución
- **Rastreo individual:** Cada distribución se registra por separado
- **Manejo de errores:** Los errores en un destinatario no afectan a los demás
- **Auditoría completa:** Registro detallado de cada envío y entrega

### 8.4. Respuestas
- **Validaciones completas:** Previene abusos y mantiene la integridad del sistema
- **Contexto mejorado:** Las respuestas incluyen información del memorando original
- **Límites de seguridad:** Protección contra bucles infinitos y respuestas excesivas

## 9. Consideraciones de Implementación

### 9.1. Datos Existentes

Si existen datos previos con el formato antiguo de correlativo, se recomienda:

1. Migrar los correlativos existentes al nuevo formato (si es necesario)
2. Mantener compatibilidad con el formato antiguo durante un período de transición
3. Actualizar las secuencias existentes para incluir el mes

### 9.2. Rendimiento

Las optimizaciones implementadas mejoran el rendimiento mediante:

- Uso de índices en campos frecuentemente consultados
- Transacciones atómicas para operaciones críticas
- Consultas optimizadas con `select_related` y `prefetch_related`

### 9.3. Seguridad

Las mejoras de seguridad incluyen:

- Códigos de verificación más largos
- Registro de metadatos de seguridad en firmas
- Validaciones exhaustivas en todos los puntos de entrada

## 10. Próximos Pasos

Para completar la implementación según los requisitos mejorados, se recomienda:

1. **Migraciones de base de datos:** Crear y ejecutar las migraciones necesarias
2. **Pruebas:** Validar el sistema correlativo con mes en entornos de prueba
3. **Notificaciones mejoradas:** Implementar sistema multi-canal de notificaciones
4. **Panel de administración:** Agregar vistas para gestionar distribuciones
5. **Reportes:** Crear reportes de distribución y seguimiento

## Conclusión

Las optimizaciones implementadas mejoran significativamente la robustez, seguridad y trazabilidad del sistema de gestión de memorandos. El nuevo formato de correlativo con mes, el sistema de distribución mejorado, las validaciones avanzadas y la firma digital con metadatos completos proporcionan una base sólida para un sistema de producción confiable y escalable.

