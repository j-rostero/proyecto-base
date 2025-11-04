from django.contrib import admin
from .models import Memo, MemoAttachment, SecuenciaMemorando


@admin.register(Memo)
class MemoAdmin(admin.ModelAdmin):
    list_display = ['numero_correlativo', 'subject', 'author', 'departamento', 'status', 'prioridad', 'created_at', 'approved_at']
    list_filter = ['status', 'prioridad', 'confidencial', 'created_at', 'departamento']
    search_fields = ['numero_correlativo', 'subject', 'body']
    readonly_fields = ['numero_correlativo', 'created_at', 'approved_at', 'fecha_distribucion', 'sello_digital']
    fieldsets = (
        ('Información básica', {
            'fields': ('numero_correlativo', 'subject', 'body', 'prioridad', 'confidencial')
        }),
        ('Relaciones', {
            'fields': ('author', 'departamento', 'approver', 'recipients', 'parent_memo')
        }),
        ('Estado y fechas', {
            'fields': ('status', 'created_at', 'approved_at', 'fecha_distribucion')
        }),
        ('Firma digital', {
            'fields': ('sello_digital', 'signed_file')
        }),
        ('Comentarios', {
            'fields': ('rejection_reason', 'modificacion_solicitada')
        }),
    )
    filter_horizontal = ['recipients']


@admin.register(MemoAttachment)
class MemoAttachmentAdmin(admin.ModelAdmin):
    list_display = ['memo', 'uploaded_by', 'file', 'file_size', 'uploaded_at']
    list_filter = ['uploaded_at']
    readonly_fields = ['file_size', 'uploaded_at']


@admin.register(SecuenciaMemorando)
class SecuenciaMemorandoAdmin(admin.ModelAdmin):
    list_display = ['departamento', 'año', 'ultima_secuencia']
    list_filter = ['año', 'departamento']
    readonly_fields = ['ultima_secuencia']

