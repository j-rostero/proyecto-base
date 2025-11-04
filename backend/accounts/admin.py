from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Departamento


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'prefijo', 'director', 'activo', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['nombre', 'prefijo']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'departamento', 'is_staff', 'is_active', 'created_at']
    list_filter = ['is_staff', 'is_active', 'role', 'departamento', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at', 'date_joined', 'last_login']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información adicional', {
            'fields': ('role', 'departamento', 'cargo')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Información adicional', {
            'fields': ('role', 'departamento', 'cargo')
        }),
    )

