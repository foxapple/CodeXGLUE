# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'JenkinsFailuresMetric'
        db.create_table('dashboard_jenkinsfailuresmetric', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('show_on_dashboard', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('show_sparkline', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('period', self.gf('django.db.models.fields.CharField')(default='instant', max_length=15)),
            ('unit', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('unit_plural', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('jenkins_root_url', self.gf('django.db.models.fields.URLField')(max_length=1000)),
            ('build_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('is_success_cnt', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_percentage', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('dashboard', ['JenkinsFailuresMetric'])

    def backwards(self, orm):
        # Deleting model 'JenkinsFailuresMetric'
        db.delete_table('dashboard_jenkinsfailuresmetric')

    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dashboard.datum': {
            'Meta': {'ordering': "['-timestamp']", 'object_name': 'Datum'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'measurement': ('django.db.models.fields.BigIntegerField', [], {}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        'dashboard.githubitemcountmetric': {
            'Meta': {'object_name': 'GithubItemCountMetric'},
            'api_url': ('django.db.models.fields.URLField', [], {'max_length': '1000'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_url': ('django.db.models.fields.URLField', [], {'max_length': '1000'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'period': ('django.db.models.fields.CharField', [], {'default': "'instant'", 'max_length': '15'}),
            'show_on_dashboard': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'show_sparkline': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'unit_plural': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dashboard.jenkinsfailuresmetric': {
            'Meta': {'object_name': 'JenkinsFailuresMetric'},
            'build_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_percentage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_success_cnt': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'jenkins_root_url': ('django.db.models.fields.URLField', [], {'max_length': '1000'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'period': ('django.db.models.fields.CharField', [], {'default': "'instant'", 'max_length': '15'}),
            'show_on_dashboard': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'show_sparkline': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'unit_plural': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dashboard.rssfeedmetric': {
            'Meta': {'object_name': 'RSSFeedMetric'},
            'feed_url': ('django.db.models.fields.URLField', [], {'max_length': '1000'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_url': ('django.db.models.fields.URLField', [], {'max_length': '1000'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'period': ('django.db.models.fields.CharField', [], {'default': "'instant'", 'max_length': '15'}),
            'show_on_dashboard': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'show_sparkline': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'unit_plural': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dashboard.tracticketmetric': {
            'Meta': {'object_name': 'TracTicketMetric'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'period': ('django.db.models.fields.CharField', [], {'default': "'instant'", 'max_length': '15'}),
            'query': ('django.db.models.fields.TextField', [], {}),
            'show_on_dashboard': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'show_sparkline': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'unit_plural': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['dashboard']