# Generated by Django 5.1.6 on 2025-03-16 02:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_remove_stacks_type_remove_stacks_variant_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stacks',
            old_name='stack',
            new_name='purchased_stack_id',
        ),
        migrations.AddField(
            model_name='stacks',
            name='github_repo',
            field=models.URLField(null=True),
        ),
        migrations.AddField(
            model_name='stacks',
            name='google_cli_key',
            field=models.TextField(blank=True),
        ),
    ]
