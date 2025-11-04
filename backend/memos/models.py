from django.db import models
from django.conf import settings


class Memo(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Borrador'
        PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pendiente de Aprobación'
        APPROVED = 'APPROVED', 'Aprobado'
        REJECTED = 'REJECTED', 'Rechazado'

    subject = models.CharField(max_length=255, verbose_name='Asunto')
    body = models.TextField(verbose_name='Contenido')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Estado'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authored_memos',
        verbose_name='Autor'
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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Aprobación')
    parent_memo = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Memo Padre'
    )
    signed_file = models.FileField(
        upload_to='signed_memos/',
        null=True,
        blank=True,
        verbose_name='Archivo Firmado'
    )
    rejection_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name='Motivo de Rechazo'
    )

    class Meta:
        db_table = 'memos'
        verbose_name = 'Memorándum'
        verbose_name_plural = 'Memorándums'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.get_status_display()}"


class MemoAttachment(models.Model):
    memo = models.ForeignKey(
        Memo,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Memo'
    )
    file = models.FileField(
        upload_to='memo_attachments/',
        verbose_name='Archivo'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Subido por'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Subida')

    class Meta:
        db_table = 'memo_attachments'
        verbose_name = 'Adjunto de Memorándum'
        verbose_name_plural = 'Adjuntos de Memorándums'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.memo.subject} - {self.file.name}"

