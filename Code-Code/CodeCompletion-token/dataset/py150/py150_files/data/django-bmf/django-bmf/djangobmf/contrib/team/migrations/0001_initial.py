# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.BMF_CONTRIB_EMPLOYEE),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Modified', null=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created', null=True)),
                ('uuid', models.CharField(blank=True, verbose_name='UUID', db_index=True, max_length=100, editable=False, null=True)),
                ('name', models.CharField(max_length=255)),
                ('created_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True, editable=False, related_name="+")),
                ('modified_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True, editable=False, related_name="+")),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Team',
                'verbose_name_plural': 'Teams',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TeamMember',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('is_manager', models.BooleanField(default=False, verbose_name='Is manager')),
                ('employee', models.ForeignKey(blank=True, related_name='+', to=settings.BMF_CONTRIB_EMPLOYEE, null=True)),
                ('team', models.ForeignKey(blank=True, related_name='+', to='djangobmf_team.Team', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='teammember',
            unique_together=set([('team', 'employee')]),
        ),
        migrations.AddField(
            model_name='team',
            name='members',
            field=models.ManyToManyField(blank=True, through='djangobmf_team.TeamMember', to=settings.BMF_CONTRIB_EMPLOYEE, related_name='teams'),
            preserve_default=True,
        ),
    ]
