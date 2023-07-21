# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ArticleTags'
        db.create_table('zorna_articles_tags', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=100)),
        ))
        db.send_create_signal('articles', ['ArticleTags'])

        # Adding model 'TaggedArticleStory'
        db.create_table('zorna_tagged_articles', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['articles.ArticleStory'])),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(related_name='articles_taggedarticlestory_items', to=orm['articles.ArticleTags'])),
        ))
        db.send_create_signal('articles', ['TaggedArticleStory'])


    def backwards(self, orm):
        # Deleting model 'ArticleTags'
        db.delete_table('zorna_articles_tags')

        # Deleting model 'TaggedArticleStory'
        db.delete_table('zorna_tagged_articles')


    models = {
        'actstream.action': {
            'Meta': {'ordering': "('-timestamp',)", 'object_name': 'Action'},
            'action_object_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'action_object'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'action_object_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'actor_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'actor'", 'to': "orm['contenttypes.ContentType']"}),
            'actor_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'target_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'target'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'target_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'verb': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'articles.articleattachments': {
            'Meta': {'object_name': 'ArticleAttachments', 'db_table': "'zorna_articles_attachments'"},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['articles.ArticleStory']", 'blank': 'True'}),
            'attached_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mimetype': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'articles.articlecategory': {
            'Meta': {'ordering': "['tree_id', 'lft']", 'object_name': 'ArticleCategory', 'db_table': "'zorna_articles_categories'"},
            'allow_comments': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email_notification': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_modifier_articles_articlecategory_related'", 'null': 'True', 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_owner_articles_articlecategory_related'", 'null': 'True', 'to': "orm['auth.User']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['articles.ArticleCategory']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'site_owner_articles_articlecategory_related'", 'null': 'True', 'to': "orm['sites.Site']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'time_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'time_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'articles.articlecomments': {
            'Meta': {'object_name': 'ArticleComments', 'db_table': "'zorna_articles_comments'"},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['articles.ArticleStory']", 'blank': 'True'}),
            'comment': ('django.db.models.fields.TextField', [], {}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_modifier_articles_articlecomments_related'", 'null': 'True', 'to': "orm['auth.User']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_owner_articles_articlecomments_related'", 'null': 'True', 'to': "orm['auth.User']"}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'site_owner_articles_articlecomments_related'", 'null': 'True', 'to': "orm['sites.Site']"}),
            'time_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'time_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'articles.articlestory': {
            'Meta': {'ordering': "['-time_updated']", 'object_name': 'ArticleStory', 'db_table': "'zorna_stories'"},
            'allow_comments': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['articles.ArticleCategory']", 'symmetrical': 'False', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'head': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'mimetype': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_modifier_articles_articlestory_related'", 'null': 'True', 'to': "orm['auth.User']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_owner_articles_articlestory_related'", 'null': 'True', 'to': "orm['auth.User']"}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'site_owner_articles_articlestory_related'", 'null': 'True', 'to': "orm['sites.Site']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1'}),
            'time_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'time_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'articles.articletags': {
            'Meta': {'ordering': "['name']", 'object_name': 'ArticleTags', 'db_table': "'zorna_articles_tags'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        'articles.taggedarticlestory': {
            'Meta': {'object_name': 'TaggedArticleStory', 'db_table': "'zorna_tagged_articles'"},
            'content_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['articles.ArticleStory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'articles_taggedarticlestory_items'", 'to': "orm['articles.ArticleTags']"})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['articles']