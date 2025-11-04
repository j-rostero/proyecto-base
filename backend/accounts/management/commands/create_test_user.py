from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea un usuario de prueba para desarrollo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='testuser',
            help='Nombre de usuario (default: testuser)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='testpass123',
            help='Contraseña (default: testpass123)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='test@example.com',
            help='Email (default: test@example.com)',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'El usuario "{username}" ya existe.')
            )
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'El email "{email}" ya está en uso.')
            )
            return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name='Usuario',
            last_name='Prueba',
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Usuario de prueba creado exitosamente!\n'
                f'  Usuario: {username}\n'
                f'  Contraseña: {password}\n'
                f'  Email: {email}'
            )
        )

