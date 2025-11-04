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

    class Meta:
        model = Memo
        fields = [
            'id', 'subject', 'body', 'status', 'author', 'approver',
            'recipients', 'created_at', 'approved_at', 'attachments_count'
        ]
        read_only_fields = ['id', 'created_at', 'approved_at']

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

    class Meta:
        model = Memo
        fields = [
            'id', 'subject', 'body', 'status', 'author', 'approver',
            'recipients', 'created_at', 'approved_at', 'parent_memo',
            'replies', 'attachments', 'signed_file_url', 'rejection_reason'
        ]
        read_only_fields = [
            'id', 'created_at', 'approved_at', 'parent_memo', 'replies'
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

    class Meta:
        model = Memo
        fields = [
            'subject', 'body', 'recipient_ids', 'approver_id'
        ]

    def create(self, validated_data):
        recipient_ids = validated_data.pop('recipient_ids', [])
        approver_id = validated_data.pop('approver_id', None)
        
        memo = Memo.objects.create(
            **validated_data,
            author=self.context['request'].user,
            status=Memo.Status.DRAFT
        )
        
        if recipient_ids:
            from accounts.models import User
            recipients = User.objects.filter(id__in=recipient_ids)
            memo.recipients.set(recipients)
        
        if approver_id:
            from accounts.models import User
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
            'subject', 'body', 'recipient_ids', 'approver_id'
        ]

    def update(self, instance, validated_data):
        recipient_ids = validated_data.pop('recipient_ids', None)
        approver_id = validated_data.pop('approver_id', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if recipient_ids is not None:
            from accounts.models import User
            recipients = User.objects.filter(id__in=recipient_ids)
            instance.recipients.set(recipients)
        
        if approver_id is not None:
            from accounts.models import User
            approver = User.objects.filter(id=approver_id).first()
            if approver:
                instance.approver = approver
        
        instance.save()
        return instance

