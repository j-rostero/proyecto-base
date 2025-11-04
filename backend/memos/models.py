from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
import json


class SecuenciaMemorando(models.Model):
    """Control de secuencias correlativas por departamento, año y mes."""
    departamento = models.ForeignKey(
        'accounts.Departamento',
        on_delete=models.CASCADE,
        related_name='secuencias',
        verbose_name='Departamento'
    )
    año = models.IntegerField(verbose_name='Año', validators=[MaxValueValidator(9999)])
    mes = models.IntegerField(
        verbose_name='Mes',
        validators=[MaxValueValidator(12), MinValueValidator(1)],
        help_text='Mes (1-12)'
    )
    ultima_secuencia = models.IntegerField(default=0, verbose_name='Última Secuencia')
    prefijo = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name='Prefijo',
        help_text='Caché del prefijo del departamento'
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')

    class Meta:
        db_table = 'secuencias_memorandos'
        verbose_name = 'Secuencia de Memorando'
        verbose_name_plural = 'Secuencias de Memorandos'
        unique_together = [['departamento', 'año', 'mes']]
        ordering = ['-año', '-mes', 'departamento']
        indexes = [
            models.Index(fields=['departamento', 'año', 'mes']),
        ]

    def __str__(self):
        return f"{self.departamento.prefijo}-{self.año}-{self.mes:02d}: {self.ultima_secuencia}"


class Memo(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Borrador'
        PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pendiente de Aprobación'
        APPROVED = 'APPROVED', 'Aprobado'
        REJECTED = 'REJECTED', 'Rechazado'
        MODIFICACION_SOLICITADA = 'MODIFICACION_SOLICITADA', 'Modificación Solicitada'
        DISTRIBUIDO = 'DISTRIBUIDO', 'Distribuido'

    class Prioridad(models.TextChoices):
        BAJA = 'baja', 'Baja'
        NORMAL = 'normal', 'Normal'
        ALTA = 'alta', 'Alta'
        URGENTE = 'urgente', 'Urgente'

    # Campos básicos
    numero_correlativo = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Número Correlativo',
        help_text='Formato: [Prefijo]-[Año]-[Mes]-[Secuencial]'
    )
    subject = models.CharField(max_length=255, verbose_name='Asunto')
    body = models.TextField(verbose_name='Contenido')
    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Estado'
    )
    prioridad = models.CharField(
        max_length=10,
        choices=Prioridad.choices,
        default=Prioridad.NORMAL,
        verbose_name='Prioridad'
    )
    confidencial = models.BooleanField(default=False, verbose_name='Confidencial')
    
    # Relaciones
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authored_memos',
        verbose_name='Autor'
    )
    departamento = models.ForeignKey(
        'accounts.Departamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='memorandos',
        verbose_name='Departamento'
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_memos',
        null=True,
        blank=True,
        verbose_name='Aprobador'
    )
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='received_memos',
        blank=True,
        verbose_name='Destinatarios'
    )
    parent_memo = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Memo Padre'
    )
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Aprobación')
    fecha_distribucion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Distribución')
    
    # Archivos
    signed_file = models.FileField(
        upload_to='signed_memos/',
        null=True,
        blank=True,
        verbose_name='Archivo Firmado'
    )
    
    # Firma digital y sello
    sello_digital = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Sello Digital',
        help_text='Contiene: director, cargo, departamento, fechaFirma, hash, codigoVerificacion'
    )
    
    # Motivos y comentarios
    rejection_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name='Motivo de Rechazo'
    )
    modificacion_solicitada = models.TextField(
        null=True,
        blank=True,
        verbose_name='Comentarios de Modificación'
    )

    class Meta:
        db_table = 'memos'
        verbose_name = 'Memorándum'
        verbose_name_plural = 'Memorándums'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['numero_correlativo']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        correlativo = self.numero_correlativo or 'Sin correlativo'
        return f"{correlativo} - {self.subject} - {self.get_status_display()}"


class MemoAttachment(models.Model):
    """Adjuntos de memorandos con validación de tamaño y formato."""
    memo = models.ForeignKey(
        Memo,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Memo'
    )
    file = models.FileField(
        upload_to='memo_attachments/',
        verbose_name='Archivo',
        help_text='Formatos permitidos: PDF, DOC, DOCX, XLS, XLSX. Máximo 10MB'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Subido por'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Subida')
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name='Tamaño del Archivo (bytes)')

    class Meta:
        db_table = 'memo_attachments'
        verbose_name = 'Adjunto de Memorándum'
        verbose_name_plural = 'Adjuntos de Memorándums'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.memo.subject} - {self.file.name}"


class DistribucionMemorando(models.Model):
    """Registro de distribución de memorandos a destinatarios."""
    class EstadoDistribucion(models.TextChoices):
        ENVIADO = 'ENVIADO', 'Enviado'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        ERROR = 'ERROR', 'Error'
        PENDIENTE = 'PENDIENTE', 'Pendiente'
    
    class MetodoDistribucion(models.TextChoices):
        SISTEMA = 'SISTEMA', 'Sistema'
        EMAIL = 'EMAIL', 'Email'
        PUSH = 'PUSH', 'Notificación Push'
    
    memorandum = models.ForeignKey(
        Memo,
        on_delete=models.CASCADE,
        related_name='distribuciones',
        verbose_name='Memorando'
    )
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='distribuciones_recibidas',
        verbose_name='Destinatario'
    )
    tipo_destinatario = models.CharField(
        max_length=20,
        default='PRINCIPAL',
        verbose_name='Tipo de Destinatario',
        help_text='PRINCIPAL o COPIA'
    )
    fecha_envio = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Envío')
    fecha_entrega = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Entrega')
    metodo = models.CharField(
        max_length=20,
        choices=MetodoDistribucion.choices,
        default=MetodoDistribucion.SISTEMA,
        verbose_name='Método de Distribución'
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoDistribucion.choices,
        default=EstadoDistribucion.ENVIADO,
        verbose_name='Estado'
    )
    error = models.TextField(null=True, blank=True, verbose_name='Mensaje de Error')
    acuse_recibo = models.BooleanField(default=False, verbose_name='Acuse de Recibo')
    fecha_acuse = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Acuse')

    class Meta:
        db_table = 'distribuciones_memorandos'
        verbose_name = 'Distribución de Memorando'
        verbose_name_plural = 'Distribuciones de Memorandos'
        ordering = ['-fecha_envio']
        indexes = [
            models.Index(fields=['memorandum', 'destinatario']),
            models.Index(fields=['estado', 'fecha_envio']),
        ]

    def __str__(self):
        return f"{self.memorandum.numero_correlativo} -> {self.destinatario.username} ({self.estado})"

