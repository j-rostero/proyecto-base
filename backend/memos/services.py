import os
import logging
import hashlib
import secrets
import json
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.conf import settings
from django.core.files import File
from django.utils import timezone
from PyPDF2 import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

# Constantes de validación mejoradas
MAX_RECIPIENTS = 15  # Actualizado según requisitos mejorados
MAX_ATTACHMENTS = 5
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB en bytes
MAX_TOTAL_SIZE = 25 * 1024 * 1024  # 25MB total
ALLOWED_ATTACHMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
MAX_BORRADORES_SIMULTANEOS = 50
TIEMPO_MAXIMO_BORRADOR = 30  # días
TIEMPO_MAXIMO_APROBACION = 72  # horas
MAX_PROFUNDIDAD_HILO = 10
MAX_RESPUESTAS_POR_MEMO = 20
TIEMPO_MAXIMO_RESPUESTA = 90  # días


def generar_correlativo(departamento, año=None, mes=None):
    """
    Genera un número correlativo único para un memorando según el formato mejorado:
    [Prefijo Departamento]-[Año]-[Mes]-[Secuencial]
    
    Ejemplo: FIN-2024-03-0042
    
    Utiliza transacciones con bloqueo para evitar duplicados concurrentes.
    """
    from .models import SecuenciaMemorando
    from django.db import transaction
    from datetime import datetime
    
    if not departamento or not departamento.prefijo:
        raise ValueError("El departamento debe tener un prefijo asignado")
    
    ahora = datetime.now()
    if año is None:
        año = ahora.year
    if mes is None:
        mes = ahora.month
    
    # Validar mes
    if not (1 <= mes <= 12):
        raise ValueError("El mes debe estar entre 1 y 12")
    
    prefijo = departamento.prefijo
    
    # Usar transacción con bloqueo SELECT FOR UPDATE para evitar condiciones de carrera
    with transaction.atomic():
        # Bloquear la fila para evitar duplicados concurrentes
        secuencia = SecuenciaMemorando.objects.select_for_update().filter(
            departamento=departamento,
            año=año,
            mes=mes
        ).first()
        
        if secuencia:
            # Incrementar la secuencia de forma atómica
            secuencia.ultima_secuencia += 1
            secuencia.actualizado_en = timezone.now()
            if not secuencia.prefijo:
                secuencia.prefijo = prefijo
            secuencia.save(update_fields=['ultima_secuencia', 'actualizado_en', 'prefijo'])
        else:
            # Crear nueva secuencia
            secuencia = SecuenciaMemorando.objects.create(
                departamento=departamento,
                año=año,
                mes=mes,
                ultima_secuencia=1,
                prefijo=prefijo
            )
    
    # Formatear el número correlativo con el formato mejorado
    secuencial_formateado = str(secuencia.ultima_secuencia).zfill(4)
    mes_formateado = str(mes).zfill(2)
    correlativo = f"{prefijo}-{año}-{mes_formateado}-{secuencial_formateado}"
    
    logger.info(f"Correlativo generado: {correlativo} para departamento {departamento.nombre}")
    return correlativo


def generar_hash_memorando(memo):
    """
    Genera un hash SHA256 del contenido del memorando para el sello digital.
    """
    contenido = {
        'numero_correlativo': memo.numero_correlativo,
        'subject': memo.subject,
        'body': memo.body,
        'author_id': memo.author.id,
        'created_at': memo.created_at.isoformat(),
        'approved_at': memo.approved_at.isoformat() if memo.approved_at else None,
    }
    
    contenido_str = json.dumps(contenido, sort_keys=True)
    hash_obj = hashlib.sha256(contenido_str.encode('utf-8'))
    return hash_obj.hexdigest()


def generar_codigo_verificacion():
    """
    Genera un código único de verificación para el sello digital.
    Utiliza un token URL-safe de 32 caracteres para mayor seguridad.
    """
    return secrets.token_urlsafe(32)


def crear_sello_digital(memo, request=None):
    """
    Crea el sello digital avanzado del memorando con metadatos completos.
    Incluye información del director, timestamp, hash, código de verificación
    y metadatos de seguridad (IP, user agent, ubicación aproximada).
    """
    if not memo.approver:
        raise ValueError("El memorando debe tener un aprobador asignado")
    
    director = memo.approver
    departamento = memo.departamento
    
    # Obtener metadatos del request si está disponible
    metadatos = {}
    if request:
        metadatos = {
            'ip': obtener_ip_cliente(request),
            'userAgent': request.META.get('HTTP_USER_AGENT', 'N/A'),
            'ubicacion': obtener_ubicacion_aproximada(request)  # Basado en IP si es posible
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


def obtener_ip_cliente(request):
    """
    Obtiene la IP real del cliente desde el request.
    Considera proxies y headers X-Forwarded-For.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'N/A')
    return ip


def obtener_ubicacion_aproximada(request):
    """
    Obtiene ubicación aproximada basada en IP.
    En producción, esto podría usar un servicio de geolocalización.
    Por ahora retorna información básica.
    """
    ip = obtener_ip_cliente(request)
    # Aquí se podría integrar un servicio de geolocalización por IP
    # Por ahora retornamos información básica
    return {
        'ip': ip,
        'nota': 'Ubicación aproximada basada en IP (requiere servicio externo)'
    }


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


def distribuir_memorando(memorando_id, request=None):
    """
    Distribuye un memorando aprobado a todos sus destinatarios.
    Crea registros de distribución y envía notificaciones.
    """
    from .models import Memo, DistribucionMemorando
    from django.db import transaction
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:
        memorando = Memo.objects.select_related('author', 'departamento', 'approver').prefetch_related('recipients').get(id=memorando_id)
    except Memo.DoesNotExist:
        raise ValueError(f"Memorando {memorando_id} no encontrado")
    
    if memorando.status != Memo.Status.APPROVED:
        raise ValueError(f"El memorando debe estar en estado APPROVED, actual: {memorando.status}")
    
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
                        subject = f'Nuevo Memorando Recibido: {memorando.subject}'
                        message = f'''
Has recibido un nuevo memorando:

Número: {memorando.numero_correlativo or "N/A"}
Asunto: {memorando.subject}
Remitente: {memorando.author.nombre_completo or memorando.author.username}
Departamento: {memorando.departamento.nombre if memorando.departamento else "N/A"}
Fecha: {memorando.approved_at.strftime("%d/%m/%Y %H:%M") if memorando.approved_at else "N/A"}

Puede acceder al memorando desde el sistema.
                        '''
                        send_mail(
                            subject,
                            message,
                            settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
                            [destinatario.email],
                            fail_silently=True,
                        )
                        
                        distribucion.estado = DistribucionMemorando.EstadoDistribucion.ENTREGADO
                        distribucion.fecha_entrega = timezone.now()
                        distribucion.save()
                        
                    except Exception as e:
                        logger.error(f'Error al enviar email a {destinatario.email}: {str(e)}')
                        distribucion.estado = DistribucionMemorando.EstadoDistribucion.ERROR
                        distribucion.error = str(e)
                        distribucion.save()
                
                resultados.append({
                    'destinatario': destinatario.nombre_completo or destinatario.username,
                    'estado': distribucion.estado,
                    'distribucionId': distribucion.id
                })
                
            except Exception as error:
                logger.error(f'Error al distribuir a {destinatario.username}: {str(error)}')
                resultados.append({
                    'destinatario': destinatario.nombre_completo or destinatario.username,
                    'estado': 'ERROR',
                    'error': str(error)
                })
        
        # Actualizar estado general del memorando
        memorando.status = Memo.Status.DISTRIBUIDO
        memorando.fecha_distribucion = timezone.now()
        memorando.save()
    
    logger.info(f"Memorando {memorando_id} distribuido a {len(resultados)} destinatarios")
    return resultados


def generate_signed_pdf(memo, attachments=None):
    """
    Genera un PDF firmado del memo, incluyendo el contenido y los adjuntos.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='black',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='black',
        spaceAfter=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor='black',
        alignment=TA_LEFT,
        spaceAfter=12
    )
    
    # Encabezado del memo
    story.append(Paragraph("MEMORÁNDUM INTERNO", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Información del memo
    if memo.numero_correlativo:
        story.append(Paragraph(f"<b>Número:</b> {memo.numero_correlativo}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph(f"<b>Asunto:</b> {memo.subject}", normal_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph(f"<b>Fecha:</b> {memo.created_at.strftime('%d/%m/%Y %H:%M')}", normal_style))
    story.append(Spacer(1, 0.1*inch))
    
    if memo.prioridad:
        prioridad_display = dict(memo.Prioridad.choices).get(memo.prioridad, memo.prioridad)
        story.append(Paragraph(f"<b>Prioridad:</b> {prioridad_display}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    if memo.confidencial:
        story.append(Paragraph("<b>CONFIDENCIAL</b>", ParagraphStyle('Confidencial', parent=normal_style, textColor='red', fontSize=12, alignment=TA_CENTER)))
        story.append(Spacer(1, 0.1*inch))
    
    if memo.author:
        story.append(Paragraph(f"<b>Autor:</b> {memo.author.get_full_name() or memo.author.username}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    if memo.approver:
        story.append(Paragraph(f"<b>Aprobador:</b> {memo.approver.get_full_name() or memo.approver.username}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    if memo.recipients.exists():
        recipients_names = ', '.join([r.get_full_name() or r.username for r in memo.recipients.all()])
        story.append(Paragraph(f"<b>Destinatarios:</b> {recipients_names}", normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # Contenido del memo
    story.append(Paragraph("<b>Contenido:</b>", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Convertir el body a HTML seguro para reportlab
    import html
    body_text = html.escape(memo.body)
    body_text = body_text.replace('\n', '<br/>')
    body_text = body_text.replace('\r', '')
    story.append(Paragraph(body_text, normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Agregar sello y firma (si existen)
    seal_path = os.path.join(settings.BASE_DIR, 'media', 'seal.png')
    signature_path = os.path.join(settings.BASE_DIR, 'media', 'signature.png')
    
    if os.path.exists(seal_path):
        try:
            seal_img = Image(seal_path, width=2*inch, height=2*inch)
            story.append(Spacer(1, 0.2*inch))
            story.append(seal_img)
        except:
            pass
    
    if os.path.exists(signature_path):
        try:
            signature_img = Image(signature_path, width=3*inch, height=1*inch)
            story.append(Spacer(1, 0.2*inch))
            story.append(signature_img)
        except:
            pass
    
    # Sello digital y firma del aprobador
    if memo.approver:
        story.append(Spacer(1, 0.5*inch))
        
        # Mostrar sello digital si existe
        if memo.sello_digital:
            sello = memo.sello_digital
            sello_text = f"""
            <b>Certificado digitalmente por:</b> {sello.get('director', 'N/A')}<br/>
            <b>Cargo:</b> {sello.get('cargo', 'N/A')}<br/>
            <b>Departamento:</b> {sello.get('departamento', 'N/A')}<br/>
            <b>Fecha:</b> {datetime.fromisoformat(sello.get('fechaFirma', '')).strftime('%d/%m/%Y %H:%M') if sello.get('fechaFirma') else 'N/A'}<br/>
            <b>Código de Verificación:</b> {sello.get('codigoVerificacion', 'N/A')}
            """
            story.append(Paragraph(
                sello_text,
                ParagraphStyle('SelloDigital', parent=normal_style, alignment=TA_RIGHT, fontSize=9, backColor='lightgray')
            ))
            story.append(Spacer(1, 0.2*inch))
        else:
            # Firma simple si no hay sello digital
            story.append(Paragraph(
                f"<b>{memo.approver.nombre_completo or memo.approver.username}</b><br/>Director",
                ParagraphStyle('Signature', parent=normal_style, alignment=TA_RIGHT)
            ))
            # Usar datetime.now() si approved_at aún no está establecido
            approval_date = memo.approved_at if memo.approved_at else datetime.now()
            story.append(Paragraph(
                f"Fecha de aprobación: {approval_date.strftime('%d/%m/%Y %H:%M')}",
                ParagraphStyle('SignatureDate', parent=normal_style, alignment=TA_RIGHT, fontSize=9)
            ))
    
    # Construir el PDF
    try:
        doc.build(story)
        buffer.seek(0)
    except Exception as e:
        logger.error(f'Error al construir PDF: {str(e)}')
        raise
    
    # Si hay adjuntos, concatenarlos
    if attachments:
        try:
            main_pdf = PdfReader(buffer)
            writer = PdfWriter()
            
            # Agregar páginas del memo principal
            for page in main_pdf.pages:
                writer.add_page(page)
            
            # Agregar páginas de los adjuntos
            for attachment in attachments:
                try:
                    # Obtener la ruta del archivo
                    if hasattr(attachment.file, 'path'):
                        file_path = attachment.file.path
                    elif hasattr(attachment.file, 'read'):
                        # Si es un objeto file, necesitamos guardarlo temporalmente o usar directamente
                        attachment.file.seek(0)
                        attachment_pdf = PdfReader(attachment.file)
                        for page in attachment_pdf.pages:
                            writer.add_page(page)
                        continue
                    else:
                        file_path = attachment.file.name
                        # Construir la ruta completa
                        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    
                    if os.path.exists(full_path):
                        with open(full_path, 'rb') as f:
                            attachment_pdf = PdfReader(f)
                            for page in attachment_pdf.pages:
                                writer.add_page(page)
                    else:
                        logger.warning(f'Archivo adjunto no encontrado: {full_path}')
                except Exception as e:
                    # Si no es PDF o hay error, se omite pero se registra
                    logger.warning(f'Error al procesar adjunto {attachment.id}: {str(e)}')
                    pass
            
            # Escribir el PDF final
            final_buffer = BytesIO()
            writer.write(final_buffer)
            final_buffer.seek(0)
            return final_buffer
        except Exception as e:
            logger.error(f'Error al concatenar adjuntos: {str(e)}')
            # Si falla la concatenación, devolver el PDF principal
            buffer.seek(0)
            return buffer
    
    return buffer

