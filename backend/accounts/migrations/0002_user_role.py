# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('SECONDARY_USER', 'Redactor'), ('DIRECTOR', 'Aprobador'), ('AREA_USER', 'Receptor')],
                default='SECONDARY_USER',
                max_length=20
            ),
        ),
    ]
