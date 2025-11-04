import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.conf import settings
from django.core.files import File
from PyPDF2 import PdfReader, PdfWriter


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
    story.append(Paragraph(f"<b>Asunto:</b> {memo.subject}", normal_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph(f"<b>Fecha:</b> {memo.created_at.strftime('%d/%m/%Y %H:%M')}", normal_style))
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
    
    # Firma del aprobador
    if memo.approver:
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"<b>{memo.approver.get_full_name() or memo.approver.username}</b><br/>Director",
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

