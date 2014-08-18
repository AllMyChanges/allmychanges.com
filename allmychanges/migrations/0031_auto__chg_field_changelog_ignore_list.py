# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Changelog.ignore_list'
        db.alter_column(u'allmychanges_changelog', 'ignore_list', self.gf('django.db.models.fields.CharField')(max_length=1000))

    def backwards(self, orm):

        # Changing field 'Changelog.ignore_list'
        db.alter_column(u'allmychanges_changelog', 'ignore_list', self.gf('django.db.models.fields.CharField')(max_length=10000))

    models = {
        u'allmychanges.changelog': {
            'Meta': {'object_name': 'Changelog'},
            'check_list': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_list': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000'}),
            'last_update_took': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'next_update_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'problem': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'processing_started_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'allmychanges.item': {
            'Meta': {'object_name': 'Item'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['allmychanges.Section']"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'allmychanges.package': {
            'Meta': {'unique_together': "(('user', 'namespace', 'name'),)", 'object_name': 'Package'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'packages'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['allmychanges.Changelog']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'namespace': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'repo': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'package'", 'unique': 'True', 'null': 'True', 'to': u"orm['allmychanges.Repo']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packages'", 'to': u"orm['allmychanges.User']"})
        },
        u'allmychanges.repo': {
            'Meta': {'object_name': 'Repo'},
            'changelog_markup': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'processing_date_finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'processing_date_started': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'processing_progress': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'processing_state': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'processing_status_message': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'requested_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'allmychanges.repoversion': {
            'Meta': {'object_name': 'RepoVersion'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'repo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': u"orm['allmychanges.Repo']"})
        },
        u'allmychanges.repoversionitem': {
            'Meta': {'object_name': 'RepoVersionItem'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['allmychanges.RepoVersion']"})
        },
        u'allmychanges.repoversionitemchange': {
            'Meta': {'object_name': 'RepoVersionItemChange'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'version_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'changes'", 'to': u"orm['allmychanges.RepoVersionItem']"})
        },
        u'allmychanges.section': {
            'Meta': {'object_name': 'Section'},
            'code_version': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sections'", 'to': u"orm['allmychanges.Version']"})
        },
        u'allmychanges.subscription': {
            'Meta': {'object_name': 'Subscription'},
            'come_from': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'allmychanges.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "'UTC'", 'max_length': '100'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '254'})
        },
        u'allmychanges.version': {
            'Meta': {'object_name': 'Version'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': u"orm['allmychanges.Changelog']"}),
            'code_version': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'discovered_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unreleased': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['allmychanges']