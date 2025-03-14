# Generated by Django 5.1.6 on 2025-03-09 21:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_site', '0006_alter_deployments_backend_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deployments',
            name='backend_id',
        ),
        migrations.RemoveField(
            model_name='deployments',
            name='database_id',
        ),
        migrations.RemoveField(
            model_name='deployments',
            name='frontend_id',
        ),
        migrations.CreateModel(
            name='DeploymentBackend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('deployment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_site.deployments')),
            ],
        ),
        migrations.CreateModel(
            name='DeploymentDatabase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uri', models.URLField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('deployment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_site.deployments')),
            ],
        ),
        migrations.CreateModel(
            name='DeploymentFrontend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('deployment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_site.deployments')),
            ],
        ),
    ]
