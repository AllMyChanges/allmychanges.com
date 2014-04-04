# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Version'
        db.create_table(u'allmychanges_version', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('changelog', self.gf('django.db.models.fields.related.ForeignKey')(related_name='versions', to=orm['allmychanges.Changelog'])),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'allmychanges', ['Version'])

        # Adding model 'Item'
        db.create_table(u'allmychanges_item', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('section', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['allmychanges.Section'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'allmychanges', ['Item'])

        # Adding model 'Changelog'
        db.create_table(u'allmychanges_changelog', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.URLField')(unique=True, max_length=200)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('processing_started_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'allmychanges', ['Changelog'])

        # Adding model 'Section'
        db.create_table(u'allmychanges_section', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sections', to=orm['allmychanges.Version'])),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'allmychanges', ['Section'])

        # Adding field 'Package.changelog'
        db.add_column(u'allmychanges_package', 'changelog',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='packages', null=True, to=orm['allmychanges.Changelog']),
                      keep_default=False)


        # Changing field 'Package.repo'
        db.alter_column(u'allmychanges_package', 'repo_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['allmychanges.Repo']))

    def backwards(self, orm):
        # Deleting model 'Version'
        db.delete_table(u'allmychanges_version')

        # Deleting model 'Item'
        db.delete_table(u'allmychanges_item')

        # Deleting model 'Changelog'
        db.delete_table(u'allmychanges_changelog')

        # Deleting model 'Section'
        db.delete_table(u'allmychanges_section')

        # Deleting field 'Package.changelog'
        db.delete_column(u'allmychanges_package', 'changelog_id')


        # Changing field 'Package.repo'
        db.alter_column(u'allmychanges_package', 'repo_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['auth.User']))

    models = {
        u'allmychanges.changelog': {
            'Meta': {'object_name': 'Changelog'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'processing_started_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'allmychanges.item': {
            'Meta': {'object_name': 'Item'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['allmychanges.Section']"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'allmychanges.package': {
            'Meta': {'object_name': 'Package'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'packages'", 'null': 'True', 'to': u"orm['allmychanges.Changelog']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'namespace': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'next_update_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'repo': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'package'", 'unique': 'True', 'null': 'True', 'to': u"orm['allmychanges.Repo']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packages'", 'to': u"orm['auth.User']"})
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sections'", 'to': u"orm['allmychanges.Version']"})
        },
        u'allmychanges.subscription': {
            'Meta': {'object_name': 'Subscription'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'allmychanges.version': {
            'Meta': {'object_name': 'Version'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': u"orm['allmychanges.Changelog']"}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['allmychanges']