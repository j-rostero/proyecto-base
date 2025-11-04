from django.contrib.auth.models import AbstractUser
from django.db import models


class Departamento(models.Model):
    """Modelo para gestionar departamentos con sus prefijos para correlativos."""
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    prefijo = models.CharField(max_length=10, unique=True, verbose_name='Prefijo', help_text='Ejemplo: FIN, RH, IT')
    director = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departamentos_dirigidos',
        verbose_name='Director'
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'departamentos'
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.prefijo})"


class User(AbstractUser):
    class Role(models.TextChoices):
        SECONDARY_USER = 'SECONDARY_USER', 'Redactor'
        DIRECTOR = 'DIRECTOR', 'Aprobador'
        AREA_USER = 'AREA_USER', 'Receptor'
        ADMIN = 'ADMIN', 'Administrador'

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.SECONDARY_USER
    )
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
        verbose_name='Departamento'
    )
    cargo = models.CharField(max_length=100, blank=True, verbose_name='Cargo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.username

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario."""
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username

