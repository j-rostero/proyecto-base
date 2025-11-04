from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Memo

# Diccionario para almacenar el estado anterior antes de guardar
_old_status_cache = {}


@receiver(pre_save, sender=Memo)
def memo_pre_save(sender, instance, **kwargs):
    """
    Guarda el estado anterior antes de guardar el memo.
    """
    if instance.pk:
        try:
            old_instance = Memo.objects.get(pk=instance.pk)
            _old_status_cache[instance.pk] = old_instance.status
        except Memo.DoesNotExist:
            _old_status_cache[instance.pk] = None
    else:
        _old_status_cache[None] = None


@receiver(post_save, sender=Memo)
def memo_status_changed(sender, instance, created, **kwargs):
    """
    Signal que se dispara cuando cambia el estado de un memo.
    Envía notificaciones por correo electrónico.
    """
    if created:
        # Memo nuevo, no hay notificación
        _old_status_cache.pop(instance.pk, None)
        return
    
    # Obtener el estado anterior del cache
    old_status = _old_status_cache.pop(instance.pk, None)
    
    # Solo notificar si el estado realmente cambió
    if old_status == instance.status:
        return
    
    # Verificar si el estado cambió a APPROVED
    if instance.status == 'APPROVED' and old_status != 'APPROVED':
        # Notificar a los recipients
        recipients = instance.recipients.all()
        if recipients:
            subject = f'Memo Aprobado: {instance.subject}'
            message = f'''
El memo "{instance.subject}" ha sido aprobado y está disponible para su revisión.

Autor: {instance.author.get_full_name() or instance.author.username}
Fecha de aprobación: {instance.approved_at.strftime("%d/%m/%Y %H:%M") if instance.approved_at else "N/A"}

Puede acceder al memo desde el sistema.
            '''
            
            recipient_emails = [r.email for r in recipients if r.email]
            if recipient_emails:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
                    recipient_emails,
                    fail_silently=True,
                )
        
        # Notificar al autor
        if instance.author.email:
            send_mail(
                f'Su memo ha sido aprobado: {instance.subject}',
                f'Su memo "{instance.subject}" ha sido aprobado por {instance.approver.get_full_name() or instance.approver.username}.',
                settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
                [instance.author.email],
                fail_silently=True,
            )
    
    # Verificar si el estado cambió a REJECTED
    elif instance.status == 'REJECTED' and old_status != 'REJECTED':
        # Notificar al autor
        if instance.author.email:
            rejection_msg = f'Su memo "{instance.subject}" ha sido rechazado.'
            if instance.rejection_reason:
                rejection_msg += f'\n\nMotivo: {instance.rejection_reason}'
            
            send_mail(
                f'Su memo ha sido rechazado: {instance.subject}',
                rejection_msg,
                settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
                [instance.author.email],
                fail_silently=True,
            )
    
    # Verificar si el estado cambió a PENDING_APPROVAL
    elif instance.status == 'PENDING_APPROVAL' and old_status != 'PENDING_APPROVAL':
        # Notificar al aprobador
        if instance.approver and instance.approver.email:
            send_mail(
                f'Nuevo memo pendiente de aprobación: {instance.subject}',
                f'El memo "{instance.subject}" de {instance.author.get_full_name() or instance.author.username} está pendiente de su aprobación.',
                settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
                [instance.approver.email],
                fail_silently=True,
            )
    
    # Verificar si el estado cambió a DISTRIBUIDO
    elif instance.status == 'DISTRIBUIDO' and old_status != 'DISTRIBUIDO':
        # Notificar a los recipients
        recipients = instance.recipients.all()
        if recipients:
            subject = f'Nuevo Memorando Recibido: {instance.subject}'
            message = f'''
Has recibido un nuevo memorando:

Número: {instance.numero_correlativo or "N/A"}
Asunto: {instance.subject}
Remitente: {instance.author.nombre_completo or instance.author.username}
Departamento: {instance.departamento.nombre if instance.departamento else "N/A"}

Puede acceder al memorando desde el sistema.
            '''
            
            recipient_emails = [r.email for r in recipients if r.email]
            if recipient_emails:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
                    recipient_emails,
                    fail_silently=True,
                )
    
    # Verificar si el estado cambió a MODIFICACION_SOLICITADA
    elif instance.status == 'MODIFICACION_SOLICITADA' and old_status != 'MODIFICACION_SOLICITADA':
        # Notificar al autor
        if instance.author.email:
            comentarios = instance.modificacion_solicitada or 'Sin comentarios específicos'
            send_mail(
                f'Modificaciones solicitadas en su memo: {instance.subject}',
                f'Su memo "{instance.subject}" requiere modificaciones.\n\nComentarios:\n{comentarios}\n\nEl memo ha sido retornado a borrador para que pueda realizar los cambios necesarios.',
                settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
                [instance.author.email],
                fail_silently=True,
            )

