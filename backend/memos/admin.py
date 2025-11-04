from django.contrib import admin
from .models import Memo, MemoAttachment


@admin.register(Memo)
class MemoAdmin(admin.ModelAdmin):
    list_display = ['subject', 'author', 'status', 'created_at', 'approved_at']
    list_filter = ['status', 'created_at']
    search_fields = ['subject', 'body']
    readonly_fields = ['created_at', 'approved_at']


@admin.register(MemoAttachment)
class MemoAttachmentAdmin(admin.ModelAdmin):
    list_display = ['memo', 'uploaded_by', 'file']
    list_filter = ['uploaded_at']

