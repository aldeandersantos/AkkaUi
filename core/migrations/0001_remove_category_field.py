# Generated migration to remove category field from SvgFile model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        # Se houver migrations anteriores, adicione aqui
        # Por exemplo: ('core', '0000_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='svgfile',
            name='category',
        ),
    ]
