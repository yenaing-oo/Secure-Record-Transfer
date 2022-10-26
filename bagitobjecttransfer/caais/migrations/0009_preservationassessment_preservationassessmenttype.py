# Generated by Django 3.2.11 on 2022-09-21 14:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('caais', '0008_rights_types'),
    ]

    operations = [
        migrations.CreateModel(
            name='MaterialAssessmentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(
                    help_text='Record the material assessment statement type in accordance with a controlled vocabulary maintained by the repository.',
                    max_length=128)),
                ('description', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name': 'Material Assessment Type',
                'verbose_name_plural': 'Material Assessment Types',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MaterialAssessmentStatement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assessment_plan', models.TextField(blank=True, default='', help_text='Record the planned response to each of the physical requirements for preservation and access to the material.')),
                ('assessment_value', models.TextField(blank=True, default='',
                                                       help_text='Record information about the assessment of the material with respect to its physical condition, dependencies, processing or access.')),
                ('assessment_note', models.TextField(blank=True, default='',
                                                      help_text='Record any other information relevant to the long-term preservation of the material.')),
                ('assessment_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='material_assessment_types', to='caais.materialassessmenttype')),
                ('metadata',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='material_assessments',
                                   to='caais.metadata')),
            ],
            options={
                'verbose_name': 'Material Assessment Statement',
                'verbose_name_plural': 'Material Assessment Statements',
            },
        ),
        migrations.CreateModel(
            name='EventType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(
                    help_text='Record the event type in accordance with a controlled vocabulary maintained by the repository',
                    max_length=128)),
                ('description', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name': 'Event Type',
                'verbose_name_plural': 'Event Types',
            },
        ),
        migrations.CreateModel(
            name='GeneralNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField(blank=True, default='',
                                          help_text='To provide an open text element for repositories to record any relevant information not accommodated elsewhere in this standard.')),
                ('metadata', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='general_note',
                                               to='caais.metadata')),
            ],
            options={
                'verbose_name': 'General Note',
                'verbose_name_plural': 'General Notes',
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_date', models.DateTimeField(auto_now_add=True)),
                ('event_agent', models.CharField(
                    help_text='Record the name of the staff member or application responsible for the event.',
                    max_length=256)),
                ('event_note', models.TextField(blank=True, default='',
                                                help_text='Record any other information relevant to describing the event.')),
                ('event_type',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_type',
                                   to='caais.eventtype')),
                ('metadata', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events',
                                               to='caais.metadata')),
            ],
            options={
                'verbose_name': 'Event',
                'verbose_name_plural': 'Events',
            },
        ),
        migrations.CreateModel(
            name='DateOfCreationOrRevision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(default='',
                                                   help_text='Record the action type in accordance with a controlled vocabulary maintained by the repository.',
                                                   max_length=255)),
                ('action_date', models.DateTimeField(auto_now_add=True,
                                                       help_text='Record the date on which the action (creation or revision) occurred.')),
                ('action_agent', models.CharField(default='',
                                                    help_text='Record the name of the staff member who performed the action (creation or revision) on the accession record.',
                                                    max_length=255)),
                ('action_note', models.TextField(blank=True, default='',
                                                   help_text='Record any information summarizing actions applied to the accession record.')),
                ('metadata',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='date_creation_revisions',
                                   to='caais.metadata')),
            ],
            options={
                'verbose_name': 'Date of Creation or Revision',
                'verbose_name_plural': 'Dates of Creation or Revision',
            },
            managers=[
                ('object', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='ControlInformation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rules_or_conventions', models.CharField(blank=True, default='',
                                                          help_text='Record information about the standards, rules or conventions that were followed when creating or maintaining the accession record. Indicate the software application if the accession record is based on a data entry template in a database or other automated system. Give the version number of the standard or software application where applicable.',
                                                          max_length=255)),
                ('level_of_detail', models.CharField(blank=True, default='',
                                                     help_text='Record the level of detail in accordance with a controlled vocabulary maintained by the repository.',
                                                     max_length=255)),
                ('language_of_record', models.CharField(blank=True, default='en',
                                                        help_text='Record the language(s) and script(s) used to create the accession record. If the content has been translated and is available in other languages, give those languages. Provide information about script only where it is common to use multiple scripts to represent a language and it is important to know which script is employed.',
                                                        max_length=20)),
                ('metadata',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='control_informations',
                                   to='caais.metadata')),
            ],
            options={
                'verbose_name': 'Control Information',
                'verbose_name_plural': 'Control Information',
            },
        ),
        migrations.RemoveField(
            model_name='controlinformation',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='dispositionauthority',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='preliminarycustodialhistory',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='preliminaryscopeandcontent',
            name='metadata',
        ),
        migrations.RenameField(
            model_name='extentstatement',
            old_name='quantity_and_unit_of_measure',
            new_name='quantity_and_type_of_units',
        ),
        migrations.RemoveField(
            model_name='extentstatement',
            name='carrier_type',
        ),
        migrations.RemoveField(
            model_name='extentstatement',
            name='content_type',
        ),
        migrations.AddField(
            model_name='metadata',
            name='accession_identifier',
            field=models.CharField(
                help_text='To uniquely and persistently identify the material. To support the location and retrieval of the material. To link all relevant information surrounding a transfer of material to a repository',
                max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='custodial_history',
            field=models.TextField(
                help_text="Provide relevant custodial history information in accordance with the repository's descriptive standard. Record the successive transfers of ownership, responsibility and/or custody of the accessioned material prior to its transfer to the repository",
                null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='disposition_authority',
            field=models.TextField(
                help_text='Record information about any legal instruments that apply to the accessioned material. Legal instruments include statutes, records schedules or disposition authorities, and donor agreements',
                null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='language_of_record',
            field=models.CharField(blank=True, default='en',
                                   help_text='Record the language(s) and script(s) used to create the accession record. If the content has been translated and is available in other languages, give those languages. Provide information about script only where it is common to use multiple scripts to represent a language and it is important to know which script is employed.',
                                   max_length=20),
        ),
        migrations.AddField(
            model_name='metadata',
            name='level_of_detail',
            field=models.CharField(blank=True, default='',
                                   help_text='Record the level of detail in accordance with a controlled vocabulary maintained by the repository.',
                                   max_length=255),
        ),
        migrations.AddField(
            model_name='metadata',
            name='rules_or_conventions',
            field=models.CharField(blank=True, default='',
                                   help_text='Record information about the standards, rules or conventions that were followed when creating or maintaining the accession record. Indicate the software application if the accession record is based on a data entry template in a database or other automated system. Give the version number of the standard or software application where applicable.',
                                   max_length=255),
        ),
        migrations.AddField(
            model_name='metadata',
            name='scope_and_content',
            field=models.TextField(
                help_text='Record a summary that includes: functions and activities that resulted in the material’s generation, dates, the geographic area to which the material pertains, subject matter, arrangement, classification, and documentary forms. This is recorded as a free text statement.',
                null=True),
        ),
        migrations.DeleteModel(
            name='CarrierType',
        ),
        migrations.DeleteModel(
            name='ContentType',
        ),
        migrations.DeleteModel(
            name='ControlInformation',
        ),
        migrations.DeleteModel(
            name='DispositionAuthority',
        ),
        migrations.DeleteModel(
            name='PreliminaryCustodialHistory',
        ),
        migrations.DeleteModel(
            name='PreliminaryScopeAndContent',
        ),
    ]
