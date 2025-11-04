from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Memo, MemoAttachment


class MemoAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = MemoAttachment
        fields = ['id', 'file', 'file_url', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class MemoListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    approver = UserSerializer(read_only=True)
    recipients = UserSerializer(many=True, read_only=True)
    attachments_count = serializers.SerializerMethodField()
    departamento = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Memo
        fields = [
            'id', 'numero_correlativo', 'subject', 'body', 'status', 'prioridad',
            'confidencial', 'author', 'approver', 'departamento', 'recipients',
            'created_at', 'approved_at', 'fecha_distribucion', 'attachments_count'
        ]
        read_only_fields = ['id', 'numero_correlativo', 'created_at', 'approved_at', 'fecha_distribucion']

    def get_attachments_count(self, obj):
        return obj.attachments.count()


class MemoDetailSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    approver = UserSerializer(read_only=True)
    recipients = UserSerializer(many=True, read_only=True)
    attachments = MemoAttachmentSerializer(many=True, read_only=True)
    parent_memo = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    signed_file_url = serializers.SerializerMethodField()
    departamento = serializers.StringRelatedField(read_only=True)
    sello_digital = serializers.JSONField(read_only=True)

    class Meta:
        model = Memo
        fields = [
            'id', 'numero_correlativo', 'subject', 'body', 'status', 'prioridad',
            'confidencial', 'author', 'approver', 'departamento', 'recipients',
            'created_at', 'approved_at', 'fecha_distribucion', 'parent_memo',
            'replies', 'attachments', 'signed_file_url', 'sello_digital',
            'rejection_reason', 'modificacion_solicitada'
        ]
        read_only_fields = [
            'id', 'numero_correlativo', 'created_at', 'approved_at',
            'fecha_distribucion', 'parent_memo', 'replies', 'sello_digital'
        ]

    def get_parent_memo(self, obj):
        if obj.parent_memo:
            return {
                'id': obj.parent_memo.id,
                'subject': obj.parent_memo.subject,
                'status': obj.parent_memo.status
            }
        return None

    def get_replies(self, obj):
        replies = obj.replies.all()
        return [
            {
                'id': reply.id,
                'subject': reply.subject,
                'status': reply.status,
                'created_at': reply.created_at
            }
            for reply in replies
        ]

    def get_signed_file_url(self, obj):
        request = self.context.get('request')
        if obj.signed_file and request:
            return request.build_absolute_uri(obj.signed_file.url)
        return None


class MemoCreateSerializer(serializers.ModelSerializer):
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    approver_id = serializers.IntegerField(write_only=True, required=False)
    departamento_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Memo
        fields = [
            'subject', 'body', 'prioridad', 'confidencial',
            'recipient_ids', 'approver_id', 'departamento_id'
        ]

    def validate_recipient_ids(self, value):
        """Valida que no exceda el límite de destinatarios."""
        from .services import MAX_RECIPIENTS
        if len(value) > MAX_RECIPIENTS:
            raise serializers.ValidationError(
                f'Máximo {MAX_RECIPIENTS} destinatarios permitidos'
            )
        return value

    def create(self, validated_data):
        from accounts.models import User, Departamento
        from .services import generar_correlativo
        
        recipient_ids = validated_data.pop('recipient_ids', [])
        approver_id = validated_data.pop('approver_id', None)
        departamento_id = validated_data.pop('departamento_id', None)
        
        user = self.context['request'].user
        
        # Obtener departamento del usuario si no se especifica
        if not departamento_id and user.departamento:
            departamento = user.departamento
        elif departamento_id:
            departamento = Departamento.objects.filter(id=departamento_id).first()
        else:
            departamento = None
        
        # Asignar aprobador automáticamente si hay departamento con director
        if not approver_id and departamento and departamento.director:
            approver_id = departamento.director.id
        
        memo = Memo.objects.create(
            **validated_data,
            author=user,
            departamento=departamento,
            status=Memo.Status.DRAFT
        )
        
        # Generar correlativo solo cuando se envíe a aprobación (no en borrador)
        # El correlativo se generará en el método submit
        
        if recipient_ids:
            recipients = User.objects.filter(id__in=recipient_ids)
            memo.recipients.set(recipients)
        
        if approver_id:
            approver = User.objects.filter(id=approver_id).first()
            if approver:
                memo.approver = approver
                memo.save()
        
        return memo


class MemoUpdateSerializer(serializers.ModelSerializer):
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    approver_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Memo
        fields = [
            'subject', 'body', 'prioridad', 'confidencial',
            'recipient_ids', 'approver_id'
        ]

    def validate_recipient_ids(self, value):
        """Valida que no exceda el límite de destinatarios."""
        from .services import MAX_RECIPIENTS
        if len(value) > MAX_RECIPIENTS:
            raise serializers.ValidationError(
                f'Máximo {MAX_RECIPIENTS} destinatarios permitidos'
            )
        return value

    def update(self, instance, validated_data):
        from accounts.models import User
        
        recipient_ids = validated_data.pop('recipient_ids', None)
        approver_id = validated_data.pop('approver_id', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if recipient_ids is not None:
            recipients = User.objects.filter(id__in=recipient_ids)
            instance.recipients.set(recipients)
        
        if approver_id is not None:
            approver = User.objects.filter(id=approver_id).first()
            if approver:
                instance.approver = approver
        
        instance.save()
        return instance

