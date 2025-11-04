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
from .services import generate_signed_pdf
from accounts.models import User


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
        
        elif status_param == 'REJECTED':
            # Memos rechazados del autor
            if user.role == 'SECONDARY_USER':
                return queryset.filter(author=user, status='REJECTED')
        
        # Por defecto, devolver memos relacionados con el usuario
        if user.role == 'SECONDARY_USER':
            return queryset.filter(author=user)
        elif user.role == 'DIRECTOR':
            return queryset.filter(Q(approver=user) | Q(status='PENDING_APPROVAL'))
        elif user.role == 'AREA_USER':
            return queryset.filter(Q(recipients=user, status='APPROVED') | Q(author=user))
        
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
        """
        memo = self.get_object()
        
        # Validar que el memo esté en estado DRAFT
        if memo.status != Memo.Status.DRAFT:
            return Response(
                {
                    'success': False,
                    'message': 'Solo se pueden enviar memos en estado borrador',
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
        if not memo.recipients.exists():
            return Response(
                {
                    'success': False,
                    'message': 'Debe asignar al menos un destinatario antes de enviar el memo',
                    'error_code': 'NO_RECIPIENTS_ASSIGNED'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        Aprobar un memo (generar PDF firmado y cambiar a APPROVED).
        """
        memo = self.get_object()
        
        if memo.status != 'PENDING_APPROVAL':
            return Response(
                {'success': False, 'message': 'Solo se pueden aprobar memos pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if memo.approver != request.user:
            return Response(
                {'success': False, 'message': 'Solo el aprobador asignado puede aprobar el memo'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Establecer fecha de aprobación
        approved_time = timezone.now()
        memo.approved_at = approved_time
        
        # Generar PDF firmado
        try:
            attachments = memo.attachments.all()
            pdf_buffer = generate_signed_pdf(memo, attachments)
            
            # Guardar el PDF firmado
            filename = f'memo_{memo.id}_signed_{approved_time.strftime("%Y%m%d_%H%M%S")}.pdf'
            memo.signed_file.save(filename, pdf_buffer, save=False)
        except Exception as e:
            # Si falla la generación del PDF, registrar el error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al generar PDF firmado para memo {memo.id}: {str(e)}')
            # Continuar sin PDF firmado - el memo se aprobará igual
            # El signal se disparará y enviará notificaciones
        
        # Actualizar estado a APPROVED (esto disparará el signal)
        memo.status = Memo.Status.APPROVED
        memo.save()
        
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
        
        if memo.status != 'PENDING_APPROVAL':
            return Response(
                {'success': False, 'message': 'Solo se pueden rechazar memos pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if memo.approver != request.user:
            return Response(
                {'success': False, 'message': 'Solo el aprobador asignado puede rechazar el memo'},
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
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reply(self, request, pk=None):
        """
        Crear un nuevo memo como respuesta (reply) al memo actual.
        """
        parent_memo = self.get_object()
        
        if parent_memo.status != 'APPROVED':
            return Response(
                {'success': False, 'message': 'Solo se pueden responder memos aprobados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que el usuario puede responder (debe ser recipient, director o author)
        can_reply = (
            request.user in parent_memo.recipients.all() or
            request.user == parent_memo.approver or
            request.user == parent_memo.author
        )
        
        if not can_reply:
            return Response(
                {'success': False, 'message': 'No tiene permisos para responder este memo'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Crear nuevo memo en DRAFT
        subject = request.data.get('subject', f'Re: {parent_memo.subject}')
        body = request.data.get('body', '')
        
        new_memo = Memo.objects.create(
            subject=subject,
            body=body,
            author=request.user,
            status=Memo.Status.DRAFT,
            parent_memo=parent_memo
        )
        
        # Copiar recipients y approver del memo padre
        new_memo.recipients.set(parent_memo.recipients.all())
        new_memo.approver = parent_memo.approver
        new_memo.save()
        
        return Response(
            {
                'success': True,
                'message': 'Memo de respuesta creado',
                'data': MemoDetailSerializer(new_memo, context={'request': request}).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanEditDraft])
    def upload_attachment(self, request, pk=None):
        """
        Subir un adjunto al memo (solo si está en DRAFT).
        """
        memo = self.get_object()
        
        if memo.status != 'DRAFT':
            return Response(
                {'success': False, 'message': 'Solo se pueden agregar adjuntos a memos en borrador'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'file' not in request.FILES:
            return Response(
                {'success': False, 'message': 'No se proporcionó ningún archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attachment = MemoAttachment.objects.create(
            memo=memo,
            file=request.FILES['file'],
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

