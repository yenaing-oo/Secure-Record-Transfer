# Generated by Django 3.2.11 on 2022-04-13 20:01
from django.contrib.auth.models import Group, Permission
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields

from caais.models import SourceType, SourceRole


def populate_initial_terms(apps, schema_editor):
    other_type, created = SourceType.objects.get_or_create(
        source_type='Other',
        description='Placeholder right to allow user to specify unique source type'
    )
    if created:
        other_type.save()

    other_role, created = SourceRole.objects.get_or_create(
        source_role='Other',
        description='Placeholder right to allow user to specify unique source role'
    )
    if created:
        other_role.save()


def populate_permissions(apps, schema_editor):
    ''' Add term permissions for archival staff '''
    emit_post_migrate_signal(1, False, 'default')
    group = Group.objects.get(name='archivist_user')
    existing_permissions = group.permissions.all()

    for codename in (
        'add_sourcetype',
        'change_sourcetype',
        'view_sourcetype',

        'add_sourcerole',
        'change_sourcerole',
        'view_sourcerole'):
        permission = Permission.objects.get(codename=codename)
        if permission not in existing_permissions:
            group.permissions.add(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('caais', '0002_auto_20220401_1057'),
    ]

    operations = [
        migrations.CreateModel(
            name='SourceConfidentiality',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_confidentiality', models.CharField(help_text='Use this element to identify source statements or source information that is for internal use only by the repository. Repositories should develop a controlled vocabulary with terms that can be  translated into clear rules for handling source information', max_length=128, null=True)),
                ('description', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name': 'Source confidentiality',
                'verbose_name_plural': 'Source confidentialities',
            },
        ),
        migrations.CreateModel(
            name='SourceRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_role', models.CharField(help_text='Record the source role (when known) in accordance with a controlled vocabulary maintained by the repository', max_length=128, null=True)),
                ('description', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name': 'Source role',
                'verbose_name_plural': 'Source roles',
            },
        ),
        migrations.CreateModel(
            name='SourceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_type', models.CharField(help_text='Record the source in accordance with a controlled vocabulary maintained by the repository', max_length=128, null=True)),
                ('description', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name': 'Source type',
                'verbose_name_plural': 'Source types',
            },
        ),
        migrations.CreateModel(
            name='PreliminaryCustodialHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preliminary_custodial_history', models.TextField(help_text="Provide relevant custodial history information in accordance with the repository's descriptive standard. Record the successive transfers of ownership, responsibility and/or custody of the accessioned material prior to its transfer to the repository")),
                ('metadata', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preliminary_custodial_histories', to='caais.metadata')),
            ],
            options={
                'verbose_name': 'Preliminary custodial history',
                'verbose_name_plural': 'Preliminary custodial histories',
            },
        ),
        migrations.AddField(
            model_name='status',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.CreateModel(
            name='SourceOfMaterial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_name', models.CharField(default='', help_text="Record the source name in accordance with the repository's descriptive standard", max_length=256)),
                ('contact_name', models.CharField(blank=True, default='', max_length=256)),
                ('job_title', models.CharField(blank=True, default='', max_length=256)),
                ('phone_number', models.CharField(max_length=32)),
                ('email_address', models.CharField(max_length=256)),
                ('address_line_1', models.CharField(blank=True, default='', max_length=256)),
                ('address_line_2', models.CharField(blank=True, default='', max_length=256)),
                ('city', models.CharField(blank=True, default='', max_length=128)),
                ('region', models.CharField(blank=True, default='', max_length=128)),
                ('postal_or_zip_code', models.CharField(blank=True, default='', max_length=16)),
                ('country', django_countries.fields.CountryField(max_length=2, null=True)),
                ('metadata', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_of_materials', to='caais.metadata')),
                ('source_confidentiality', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source_of_materials', to='caais.sourceconfidentiality')),
                ('source_role', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source_of_materials', to='caais.sourcerole')),
                ('source_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source_of_materials', to='caais.sourcetype')),
                ('source_note', models.TextField(blank=True, default='', help_text='Record any other information about the source of the accessioned materials. If the source performed the role for only a specific period of time (e.g. was a custodian for several years), record the dates in this element')),
            ],
            options={
                'verbose_name': 'Source of material',
                'verbose_name_plural': 'Sources of material',
            },
        ),

        # migrations.RunPython(populate_initial_terms),
        # migrations.RunPython(populate_permissions),
    ]
