# Generated by Django 4.2.3 on 2024-03-12 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('my_saiyoai', '0009_alter_improvementsuggestion_job_posting'),
    ]

    operations = [
        migrations.AddField(
            model_name='improvementsuggestion',
            name='edited_text',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='improvementsuggestion',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
