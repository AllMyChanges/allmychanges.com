# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Preview.log'
        db.add_column(u'allmychanges_preview', 'log',
                      self.gf('jsonfield.fields.JSONField')(default=[], blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Preview.log'
        db.delete_column(u'allmychanges_preview', 'log')


    models = {
        u'allmychanges.appstorebatch': {
            'Meta': {'object_name': 'AppStoreBatch'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'allmychanges.appstoreurl': {
            'Meta': {'object_name': 'AppStoreUrl'},
            'autocomplete_data': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'appstore_url'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['allmychanges.AutocompleteData']", 'blank': 'True', 'unique': 'True'}),
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'urls'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['allmychanges.AppStoreBatch']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rating': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'rating_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'allmychanges.autocompletedata': {
            'Meta': {'object_name': 'AutocompleteData'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'autocomplete'", 'null': 'True', 'to': u"orm['allmychanges.Changelog']"}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'icon': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'origin': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'source': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'allmychanges.autocompleteword': {
            'Meta': {'object_name': 'AutocompleteWord'},
            'data': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'words'", 'to': u"orm['allmychanges.AutocompleteData']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'word': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'})
        },
        u'allmychanges.autocompleteword2': {
            'Meta': {'object_name': 'AutocompleteWord2'},
            'data_objects': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'words2'", 'symmetrical': 'False', 'to': u"orm['allmychanges.AutocompleteData']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'word': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'allmychanges.changelog': {
            'Meta': {'unique_together': "(('namespace', 'name'),)", 'object_name': 'Changelog'},
            'check_list': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'downloader': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'icon': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
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
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'xslt': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        u'allmychanges.changelogskip': {
            'Meta': {'object_name': 'ChangelogSkip'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['allmychanges.Changelog']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['allmychanges.User']"})
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
        u'allmychanges.emailverificationcode': {
            'Meta': {'object_name': 'EmailVerificationCode'},
            'deployed_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'email_verification_code'", 'unique': 'True', 'to': u"orm['allmychanges.User']"})
        },
        u'allmychanges.issue': {
            'Meta': {'object_name': 'Issue'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'issues'", 'null': 'True', 'to': u"orm['allmychanges.Changelog']"}),
            'comment': ('django.db.models.fields.TextField', [], {}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'light_user': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
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
        u'allmychanges.lightmoderator': {
            'Meta': {'object_name': 'LightModerator'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'light_moderators'", 'to': u"orm['allmychanges.Changelog']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'light_user': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        },
        u'allmychanges.mandrillmessage': {
            'Meta': {'object_name': 'MandrillMessage'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mid': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {}),
            'timestamp': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'mandrill_messages'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['allmychanges.User']"})
        },
        u'allmychanges.moderator': {
            'Meta': {'object_name': 'Moderator'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['allmychanges.Changelog']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_light_user': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['allmychanges.User']"})
        },
        u'allmychanges.preview': {
            'Meta': {'object_name': 'Preview'},
            'changelog': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'previews'", 'to': u"orm['allmychanges.Changelog']"}),
            'check_list': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'done': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'downloader': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_list': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'light_user': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'log': ('jsonfield.fields.JSONField', [], {'default': '[]', 'blank': 'True'}),
            'problem': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'processing_status': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'search_list': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'source': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '40'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'previews'", 'null': 'True', 'to': u"orm['allmychanges.User']"}),
            'xslt': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
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
            'email_is_valid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'moderated_changelogs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'moderators'", 'symmetrical': 'False', 'through': u"orm['allmychanges.Moderator']", 'to': u"orm['allmychanges.Changelog']"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'rss_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'send_digest': ('django.db.models.fields.CharField', [], {'default': "'daily'", 'max_length': '100'}),
            'skips_changelogs': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'skipped_by'", 'symmetrical': 'False', 'through': u"orm['allmychanges.ChangelogSkip']", 'to': u"orm['allmychanges.Changelog']"}),
            'slack_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '2000', 'blank': 'True'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "'UTC'", 'max_length': '100'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '254'}),
            'webhook_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '2000', 'blank': 'True'})
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
        u'allmychanges.userstatehistory': {
            'Meta': {'object_name': 'UserStateHistory'},
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'state_history'", 'to': u"orm['allmychanges.User']"})
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
            'order_idx': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'preview': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'versions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['allmychanges.Preview']"}),
            'processed_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'raw_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'tweet_id': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'unreleased': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['allmychanges']