from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from .models import Memo, MemoAttachment
from .serializers import (
    MemoListSerializer,
    MemoDetailSerializer,
    MemoCreateSerializer,
    MemoUpdateSerializer,
    MemoAttachmentSerializer
)
from .permissions import (
    IsSecondaryUser,
    IsDirector,
    IsRecipientOrInvolved,
    CanEditDraft
)
from .services import (
    generate_signed_pdf, generar_correlativo, crear_sello_digital,
    MAX_RECIPIENTS, MAX_ATTACHMENTS, MAX_FILE_SIZE, ALLOWED_ATTACHMENT_EXTENSIONS
)
import logging
from accounts.models import User
import os

logger = logging.getLogger(__name__)


class MemoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar memos.
    """
    queryset = Memo.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MemoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MemoUpdateSerializer
        elif self.action == 'retrieve':
            return MemoDetailSerializer
        return MemoListSerializer
    
    def get_queryset(self):
        """
        Filtra los memos según el rol del usuario y el parámetro status.
        """
        user = self.request.user
        status_param = self.request.query_params.get('status', None)
        queryset = Memo.objects.select_related('author', 'approver').prefetch_related('recipients', 'attachments')
        
        if status_param == 'DRAFT':
            # Solo borradores del autor
            if user.role == 'SECONDARY_USER':
                return queryset.filter(author=user, status='DRAFT')
        
        elif status_param == 'PENDING_APPROVAL':
            # Memos pendientes para directores
            if user.role == 'DIRECTOR':
                return queryset.filter(status='PENDING_APPROVAL', approver=user)
        
        elif status_param == 'APPROVED':
            # Memos aprobados para receptores o autores
            if user.role == 'AREA_USER':
                return queryset.filter(status='APPROVED', recipients=user)
            elif user.role == 'DIRECTOR':
                return queryset.filter(status='APPROVED', approver=user)
            elif user.role == 'SECONDARY_USER':
                return queryset.filter(status='APPROVED', author=user)
        
        elif status_param == 'DISTRIBUIDO':
            # Memos distribuidos para receptores
            if user.role == 'AREA_USER':
                return queryset.filter(status='DISTRIBUIDO', recipients=user)
            elif user.role == 'DIRECTOR':
                return queryset.filter(status='DISTRIBUIDO', approver=user)
            elif user.role == 'SECONDARY_USER':
                return queryset.filter(status='DISTRIBUIDO', author=user)
        
        elif status_param == 'REJECTED':
            # Memos rechazados del autor
            if user.role == 'SECONDARY_USER':
                return queryset.filter(author=user, status='REJECTED')
        
        elif status_param == 'MODIFICACION_SOLICITADA':
            # Memos con modificación solicitada
            if user.role == 'SECONDARY_USER':
                return queryset.filter(author=user, status='MODIFICACION_SOLICITADA')
        
        # Por defecto, devolver memos relacionados con el usuario
        if user.role == 'SECONDARY_USER':
            return queryset.filter(author=user)
        elif user.role == 'DIRECTOR':
            return queryset.filter(Q(approver=user) | Q(status='PENDING_APPROVAL', departamento=user.departamento))
        elif user.role == 'AREA_USER':
            return queryset.filter(Q(recipients=user, status__in=['APPROVED', 'DISTRIBUIDO']) | Q(author=user))
        
        return queryset.none()
    
    def get_permissions(self):
        """
        Asigna permisos según la acción.
        """
        if self.action == 'create':
            permission_classes = [IsAuthenticated, IsSecondaryUser]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, CanEditDraft]
        elif self.action == 'retrieve':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """
        Crear un nuevo memo (solo SECONDARY_USER).
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        memo = serializer.save()
        
        return Response(
            {
                'success': True,
                'message': 'Memo creado exitosamente',
                'data': MemoDetailSerializer(memo, context={'request': request}).data
            },
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """
        Actualizar un memo (solo si está en DRAFT y es el autor).
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        memo = serializer.save()
        
        return Response(
            {
                'success': True,
                'message': 'Memo actualizado exitosamente',
                'data': MemoDetailSerializer(memo, context={'request': request}).data
            }
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSecondaryUser])
    def submit(self, request, pk=None):
        """
        Enviar memo a aprobación (cambiar de DRAFT a PENDING_APPROVAL).
        Genera el correlativo automáticamente.
        """
        memo = self.get_object()
        
        # Validar que el memo esté en estado DRAFT o MODIFICACION_SOLICITADA
        if memo.status not in [Memo.Status.DRAFT, Memo.Status.MODIFICACION_SOLICITADA]:
            return Response(
                {
                    'success': False,
                    'message': 'Solo se pueden enviar memos en estado borrador o con modificación solicitada',
                    'current_status': memo.status
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el usuario sea el autor
        if memo.author != request.user:
            return Response(
                {
                    'success': False,
                    'message': 'Solo el autor puede enviar el memo',
                    'author_id': memo.author.id,
                    'user_id': request.user.id
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar campos obligatorios
        if not memo.subject or len(memo.subject.strip()) == 0:
            return Response(
                {
                    'success': False,
                    'message': 'El asunto es obligatorio',
                    'error_code': 'SUBJECT_REQUIRED'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not memo.body or len(memo.body.strip()) < 10:
            return Response(
                {
                    'success': False,
                    'message': 'El contenido debe tener al menos 10 caracteres',
                    'error_code': 'BODY_TOO_SHORT'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que tenga un aprobador asignado
        if not memo.approver:
            return Response(
                {
                    'success': False,
                    'message': 'Debe asignar un aprobador antes de enviar el memo a aprobación',
                    'error_code': 'NO_APPROVER_ASSIGNED'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que tenga al menos un destinatario
        recipients_count = memo.recipients.count()
        if recipients_count == 0:
            return Response(
                {
                    'success': False,
                    'message': 'Debe asignar al menos un destinatario antes de enviar el memo',
                    'error_code': 'NO_RECIPIENTS_ASSIGNED'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar límite de destinatarios
        if recipients_count > MAX_RECIPIENTS:
            return Response(
                {
                    'success': False,
                    'message': f'Máximo {MAX_RECIPIENTS} destinatarios permitidos',
                    'error_code': 'TOO_MANY_RECIPIENTS'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generar correlativo si no existe (formato mejorado con mes)
        if not memo.numero_correlativo and memo.departamento:
            try:
                memo.numero_correlativo = generar_correlativo(memo.departamento)
            except Exception as e:
                return Response(
                    {
                        'success': False,
                        'message': f'Error al generar correlativo: {str(e)}',
                        'error_code': 'CORRELATIVE_GENERATION_ERROR'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Limpiar comentarios de modificación si existían
        if memo.status == Memo.Status.MODIFICACION_SOLICITADA:
            memo.modificacion_solicitada = None
        
        # Cambiar el estado a PENDING_APPROVAL
        memo.status = Memo.Status.PENDING_APPROVAL
        memo.save()
        
        return Response(
            {
                'success': True,
                'message': 'Memo enviado a aprobación exitosamente',
                'data': MemoDetailSerializer(memo, context={'request': request}).data
            }
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDirector])
    def approve(self, request, pk=None):
        """
        Aprobar un memo (generar PDF firmado, crear sello digital y cambiar a APPROVED).
        Luego se distribuye automáticamente (cambia a DISTRIBUIDO).
        """
        memo = self.get_object()
        
        if memo.status != Memo.Status.PENDING_APPROVAL:
            return Response(
                {'success': False, 'message': 'Solo se pueden aprobar memos pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if memo.approver != request.user:
            return Response(
                {'success': False, 'message': 'Solo el aprobador asignado puede aprobar el memo'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar que el director pertenezca al mismo departamento
        if memo.departamento and request.user.departamento != memo.departamento:
            return Response(
                {'success': False, 'message': 'Solo el director del departamento puede aprobar este memo'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Establecer fecha de aprobación
        approved_time = timezone.now()
        memo.approved_at = approved_time
        
        # Crear sello digital avanzado con metadatos
        try:
            memo.sello_digital = crear_sello_digital(memo, request)
        except Exception as e:
            logger.error(f'Error al crear sello digital para memo {memo.id}: {str(e)}')
            # Continuar sin sello digital
        
        # Generar PDF firmado
        try:
            attachments = memo.attachments.all()
            pdf_buffer = generate_signed_pdf(memo, attachments)
            
            # Guardar el PDF firmado
            filename = f'memo_{memo.id}_signed_{approved_time.strftime("%Y%m%d_%H%M%S")}.pdf'
            memo.signed_file.save(filename, pdf_buffer, save=False)
        except Exception as e:
            # Si falla la generación del PDF, registrar el error
            logger.error(f'Error al generar PDF firmado para memo {memo.id}: {str(e)}')
            # Continuar sin PDF firmado - el memo se aprobará igual
        
        # Actualizar estado a APPROVED (esto disparará el signal)
        memo.status = Memo.Status.APPROVED
        memo.save()
        
        # Distribuir automáticamente usando el sistema mejorado
        try:
            from .services import distribuir_memorando
            resultados_distribucion = distribuir_memorando(memo.id, request)
            logger.info(f"Memorando {memo.id} distribuido: {resultados_distribucion}")
        except Exception as e:
            logger.error(f'Error al distribuir memorando {memo.id}: {str(e)}')
            # Continuar - el memo ya está aprobado
        
        return Response(
            {
                'success': True,
                'message': 'Memo aprobado y distribuido',
                'data': MemoDetailSerializer(memo, context={'request': request}).data
            }
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDirector])
    def reject(self, request, pk=None):
        """
        Rechazar un memo.
        """
        memo = self.get_object()
        
        if memo.status != Memo.Status.PENDING_APPROVAL:
            return Response(
                {'success': False, 'message': 'Solo se pueden rechazar memos pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if memo.approver != request.user:
            return Response(
                {'success': False, 'message': 'Solo el aprobador asignado puede rechazar el memo'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar que el director pertenezca al mismo departamento
        if memo.departamento and request.user.departamento != memo.departamento:
            return Response(
                {'success': False, 'message': 'Solo el director del departamento puede rechazar este memo'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        rejection_reason = request.data.get('rejection_reason', '')
        memo.status = Memo.Status.REJECTED
        memo.rejection_reason = rejection_reason
        memo.save()
        
        return Response(
            {
                'success': True,
                'message': 'Memo rechazado',
                'data': MemoDetailSerializer(memo, context={'request': request}).data
            }
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDirector])
    def solicitar_modificaciones(self, request, pk=None):
        """
        Solicitar modificaciones a un memo (retornar a borrador con comentarios).
        """
        memo = self.get_object()
        
        if memo.status != Memo.Status.PENDING_APPROVAL:
            return Response(
                {'success': False, 'message': 'Solo se pueden solicitar modificaciones a memos pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if memo.approver != request.user:
            return Response(
                {'success': False, 'message': 'Solo el aprobador asignado puede solicitar modificaciones'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar que el director pertenezca al mismo departamento
        if memo.departamento and request.user.departamento != memo.departamento:
            return Response(
                {'success': False, 'message': 'Solo el director del departamento puede solicitar modificaciones'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        modificacion_comentarios = request.data.get('comentarios', '')
        if not modificacion_comentarios:
            return Response(
                {'success': False, 'message': 'Debe proporcionar comentarios sobre las modificaciones solicitadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        memo.status = Memo.Status.MODIFICACION_SOLICITADA
        memo.modificacion_solicitada = modificacion_comentarios
        memo.save()
        
        return Response(
            {
                'success': True,
                'message': 'Modificaciones solicitadas. El memo ha sido retornado a borrador.',
                'data': MemoDetailSerializer(memo, context={'request': request}).data
            }
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reply(self, request, pk=None):
        """
        Crear un nuevo memo como respuesta mejorada al memo actual.
        Incluye validaciones avanzadas y mejor manejo de contexto.
        """
        from .services import (
            MAX_PROFUNDIDAD_HILO, MAX_RESPUESTAS_POR_MEMO, TIEMPO_MAXIMO_RESPUESTA,
            calcular_profundidad_hilo, contar_respuestas_memo, generar_contenido_respuesta
        )
        from django.utils import timezone
        from datetime import timedelta
        
        parent_memo = self.get_object()
        
        # Validar estado del memorando padre
        if parent_memo.status != Memo.Status.DISTRIBUIDO:
            return Response(
                {'success': False, 'message': 'Solo se pueden responder memos distribuidos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que el usuario puede responder (debe ser recipient)
        can_reply = request.user in parent_memo.recipients.all()
        
        if not can_reply:
            return Response(
                {'success': False, 'message': 'Solo los destinatarios pueden responder este memo'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar tiempo máximo de respuesta (90 días desde distribución)
        if parent_memo.fecha_distribucion:
            tiempo_transcurrido = timezone.now() - parent_memo.fecha_distribucion
            if tiempo_transcurrido.days > TIEMPO_MAXIMO_RESPUESTA:
                return Response(
                    {
                        'success': False,
                        'message': f'El tiempo máximo para responder ({TIEMPO_MAXIMO_RESPUESTA} días) ha expirado'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validar profundidad del hilo
        profundidad = calcular_profundidad_hilo(parent_memo)
        if profundidad >= MAX_PROFUNDIDAD_HILO:
            return Response(
                {
                    'success': False,
                    'message': f'Se ha alcanzado la profundidad máxima del hilo ({MAX_PROFUNDIDAD_HILO} niveles)'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar número máximo de respuestas
        total_respuestas = contar_respuestas_memo(parent_memo)
        if total_respuestas >= MAX_RESPUESTAS_POR_MEMO:
            return Response(
                {
                    'success': False,
                    'message': f'Se ha alcanzado el máximo de respuestas permitidas ({MAX_RESPUESTAS_POR_MEMO})'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si ya existe una respuesta del usuario
        respuesta_existente = Memo.objects.filter(
            parent_memo=parent_memo,
            author=request.user
        ).exists()
        
        if respuesta_existente:
            return Response(
                {
                    'success': False,
                    'message': 'Ya ha respondido a este memorando'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear nuevo memo en DRAFT con contexto mejorado
        subject = request.data.get('subject', f'RE: {parent_memo.subject}')
        body = request.data.get('body', '')
        
        # Generar contenido de respuesta con contexto del memorando original
        if not body:
            body = generar_contenido_respuesta(parent_memo)
        
        # Establecer destinatario como el remitente original más otros opcionales
        new_recipients = [parent_memo.author]
        additional_recipients = request.data.get('additional_recipients', [])
        incluir_todos = request.data.get('incluir_todos_destinatarios', False)
        
        if incluir_todos:
            # Incluir todos los destinatarios del original excepto el que responde
            for dest in parent_memo.recipients.all():
                if dest.id != request.user.id and dest not in new_recipients:
                    new_recipients.append(dest)
        
        if additional_recipients:
            from accounts.models import User
            additional_users = User.objects.filter(id__in=additional_recipients)
            for user in additional_users:
                if user not in new_recipients:
                    new_recipients.append(user)
        
        new_memo = Memo.objects.create(
            subject=subject,
            body=body,
            author=request.user,
            status=Memo.Status.DRAFT,
            parent_memo=parent_memo,
            departamento=request.user.departamento,
            prioridad=parent_memo.prioridad,
            confidencial=parent_memo.confidencial
        )
        
        # Asignar destinatarios
        new_memo.recipients.set(new_recipients)
        
        # Asignar aprobador del departamento del autor
        if request.user.departamento and request.user.departamento.director:
            new_memo.approver = request.user.departamento.director
        
        # Agregar metadatos de respuesta
        import json
        metadatos = {
            'es_respuesta': True,
            'memorando_original': parent_memo.numero_correlativo,
            'respondido_por': request.user.nombre_completo or request.user.username,
            'fecha_respuesta': timezone.now().isoformat()
        }
        # El campo metadatos no existe en el modelo, pero podemos agregarlo al sello_digital temporalmente
        # o crear un campo JSONField adicional en el modelo
        
        new_memo.save()
        
        return Response(
            {
                'success': True,
                'message': 'Memo de respuesta creado exitosamente',
                'data': MemoDetailSerializer(new_memo, context={'request': request}).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanEditDraft])
    def upload_attachment(self, request, pk=None):
        """
        Subir un adjunto al memo (solo si está en DRAFT o MODIFICACION_SOLICITADA).
        Valida formato, tamaño y límite de adjuntos.
        """
        memo = self.get_object()
        
        if memo.status not in [Memo.Status.DRAFT, Memo.Status.MODIFICACION_SOLICITADA]:
            return Response(
                {'success': False, 'message': 'Solo se pueden agregar adjuntos a memos en borrador'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'file' not in request.FILES:
            return Response(
                {'success': False, 'message': 'No se proporcionó ningún archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        
        # Validar límite de adjuntos
        current_attachments_count = memo.attachments.count()
        if current_attachments_count >= MAX_ATTACHMENTS:
            return Response(
                {
                    'success': False,
                    'message': f'Máximo {MAX_ATTACHMENTS} archivos adjuntos permitidos'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar tamaño del archivo
        if file.size > MAX_FILE_SIZE:
            size_mb = MAX_FILE_SIZE / (1024 * 1024)
            return Response(
                {
                    'success': False,
                    'message': f'El archivo excede el tamaño máximo de {size_mb}MB'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar extensión del archivo
        file_name = file.name.lower()
        file_extension = os.path.splitext(file_name)[1]
        if file_extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
            return Response(
                {
                    'success': False,
                    'message': f'Formato no permitido. Formatos permitidos: {", ".join(ALLOWED_ATTACHMENT_EXTENSIONS)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attachment = MemoAttachment.objects.create(
            memo=memo,
            file=file,
            uploaded_by=request.user
        )
        
        return Response(
            {
                'success': True,
                'message': 'Adjunto subido exitosamente',
                'data': MemoAttachmentSerializer(attachment, context={'request': request}).data
            },
            status=status.HTTP_201_CREATED
        )

