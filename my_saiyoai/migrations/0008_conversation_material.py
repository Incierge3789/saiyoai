# Generated by Django 4.2.3 on 2024-03-05 02:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('my_saiyoai', '0007_conversation'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='material',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='my_saiyoai.material'),
        ),
    ]
