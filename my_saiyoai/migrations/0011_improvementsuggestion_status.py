# Generated by Django 4.2.3 on 2024-03-12 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('my_saiyoai', '0010_improvementsuggestion_edited_text_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='improvementsuggestion',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active', max_length=10),
        ),
    ]
