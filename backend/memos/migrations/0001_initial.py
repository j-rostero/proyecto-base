# Generated manually
from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0002_user_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='Memo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255, verbose_name='Asunto')),
                ('body', models.TextField(verbose_name='Contenido')),
                ('status', models.CharField(
                    choices=[
                        ('DRAFT', 'Borrador'),
                        ('PENDING_APPROVAL', 'Pendiente de Aprobación'),
                        ('APPROVED', 'Aprobado'),
                        ('REJECTED', 'Rechazado')
                    ],
                    default='DRAFT',
                    max_length=20,
                    verbose_name='Estado'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('approved_at', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de Aprobación')),
                ('signed_file', models.FileField(blank=True, null=True, upload_to='signed_memos/', verbose_name='Archivo Firmado')),
                ('rejection_reason', models.TextField(blank=True, null=True, verbose_name='Motivo de Rechazo')),
                ('approver', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='approved_memos',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Aprobador'
                )),
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='authored_memos',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Autor'
                )),
                ('parent_memo', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='replies',
                    to='memos.memo',
                    verbose_name='Memo Padre'
                )),
                ('recipients', models.ManyToManyField(
                    blank=True,
                    related_name='received_memos',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Destinatarios'
                )),
            ],
            options={
                'verbose_name': 'Memorándum',
                'verbose_name_plural': 'Memorándums',
                'db_table': 'memos',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MemoAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='memo_attachments/', verbose_name='Archivo')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Subida')),
                ('memo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attachments',
                    to='memos.memo',
                    verbose_name='Memo'
                )),
                ('uploaded_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Subido por'
                )),
            ],
            options={
                'verbose_name': 'Adjunto de Memorándum',
                'verbose_name_plural': 'Adjuntos de Memorándums',
                'db_table': 'memo_attachments',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]

