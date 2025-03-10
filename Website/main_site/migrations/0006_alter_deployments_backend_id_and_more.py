# Generated by Django 5.1.6 on 2025-03-06 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_site', '0005_remove_deployments_stack_type_deployments_stack'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deployments',
            name='backend_id',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='deployments',
            name='database_id',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='deployments',
            name='frontend_id',
            field=models.CharField(max_length=255),
        ),
    ]
