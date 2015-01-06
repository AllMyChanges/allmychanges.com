# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Version.last_seen_at'
        db.add_column(u'allmychanges_version', 'last_seen_at',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)


        # Changing field 'Changelog.source'
        db.alter_column(u'allmychanges_changelog', 'source', self.gf('allmychanges.models.URLField')(unique=True, max_length=200))

    def backwards(self, orm):
        # Deleting field 'Version.last_seen_at'
        db.delete_column(u'allmychanges_version', 'last_seen_at')


        # Changing field 'Changelog.source'
        db.alter_column(u'allmychanges_changelog', 'source', self.gf('django.db.models.fields.URLField')(max_length=200, unique=True))

    models = {
        u'allmychanges.changelog': {
            'Meta': {'unique_together': "(('namespace', 'name'),)", 'object_name': 'Changelog'},
            'check_list': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'downloader': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_list': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'last_update_took': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'namespace': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'next_update_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'paused_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'problem': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'processing_started_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'processing_status': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'search_list': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'source': ('allmychanges.models.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '40'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'allmychanges.changelogtrack': {
            'Meta': {'object_name': 'ChangelogTrack'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['allmychanges.Changelog']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['allmychanges.User']"})
        },
        u'allmychanges.deploymenthistory': {
            'Meta': {'object_name': 'DeploymentHistory'},
            'deployed_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'hash': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'allmychanges.discoveryhistory': {
            'Meta': {'object_name': 'DiscoveryHistory'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'discovery_history'", 'to': u"orm['allmychanges.Changelog']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'discovered_versions': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_versions': ('django.db.models.fields.TextField', [], {}),
            'num_discovered_versions': ('django.db.models.fields.IntegerField', [], {}),
            'num_new_versions': ('django.db.models.fields.IntegerField', [], {})
        },
        u'allmychanges.issue': {
            'Meta': {'object_name': 'Issue'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issues'", 'to': u"orm['allmychanges.Changelog']"}),
            'comment': ('django.db.models.fields.TextField', [], {}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'light_user': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'related_versions': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'resolved_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['allmychanges.User']", 'null': 'True', 'blank': 'True'})
        },
        u'allmychanges.issuecomment': {
            'Meta': {'object_name': 'IssueComment'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['allmychanges.Issue']"}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'issue_comments'", 'null': 'True', 'to': u"orm['allmychanges.User']"})
        },
        u'allmychanges.item': {
            'Meta': {'object_name': 'Item'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['allmychanges.Section']"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'allmychanges.lightmoderator': {
            'Meta': {'object_name': 'LightModerator'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'light_moderators'", 'to': u"orm['allmychanges.Changelog']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'light_user': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        },
        u'allmychanges.moderator': {
            'Meta': {'object_name': 'Moderator'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['allmychanges.Changelog']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_light_user': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['allmychanges.User']"})
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
        u'allmychanges.preview': {
            'Meta': {'object_name': 'Preview'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'previews'", 'to': u"orm['allmychanges.Changelog']"}),
            'check_list': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'done': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'downloader': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_list': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'light_user': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'problem': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'processing_status': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'search_list': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'source': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '40'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'previews'", 'null': 'True', 'to': u"orm['allmychanges.User']"})
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
            'changelogs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'trackers'", 'symmetrical': 'False', 'through': u"orm['allmychanges.ChangelogTrack']", 'to': u"orm['allmychanges.Changelog']"}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'moderated_changelogs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'moderators'", 'symmetrical': 'False', 'through': u"orm['allmychanges.Moderator']", 'to': u"orm['allmychanges.Changelog']"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "'UTC'", 'max_length': '100'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '254'})
        },
        u'allmychanges.userhistorylog': {
            'Meta': {'object_name': 'UserHistoryLog'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'light_user': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'history_log'", 'null': 'True', 'to': u"orm['allmychanges.User']"})
        },
        u'allmychanges.version': {
            'Meta': {'object_name': 'Version'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'versions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['allmychanges.Changelog']"}),
            'code_version': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'discovered_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_seen_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'preview': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'versions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['allmychanges.Preview']"}),
            'unreleased': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['allmychanges']