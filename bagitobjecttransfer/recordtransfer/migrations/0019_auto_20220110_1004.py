# Generated by Django 3.1.8 on 2022-01-10 16:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recordtransfer', '0018_sourcerole_sourcetype'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bag',
            name='review_status',
        ),
        migrations.RemoveField(
            model_name='bag',
            name='user',
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submission_date', models.DateTimeField()),
                ('review_status', models.CharField(choices=[('NR', 'Not Reviewed'), ('RS', 'Review Started'), ('RC', 'Review Complete')], default='NR', max_length=2)),
                ('accession_identifier', models.CharField(max_length=128, null=True)),
                ('level_of_detail', models.CharField(choices=[('NS', 'Not Specified'), ('ML', 'Minimal'), ('PL', 'Partial'), ('FL', 'Full')], default='NS', max_length=2)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Appraisal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appraisal_type', models.CharField(choices=[('AP', 'Archival Appraisal'), ('MP', 'Monetary Appraisal')], max_length=2)),
                ('statement', models.TextField()),
                ('note', models.TextField(null=True)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recordtransfer.submission')),
            ],
        ),
        migrations.AddField(
            model_name='bag',
            name='submission',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='recordtransfer.submission'),
        ),
    ]
