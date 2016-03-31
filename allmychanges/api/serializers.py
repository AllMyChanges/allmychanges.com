# -*- coding: utf-8 -*-
from rest_framework import serializers, fields, exceptions
from rest_framework_extensions.fields import ResourceUriField
from django.core.exceptions import ValidationError

from allmychanges.models import (
    Preview,
    Subscription,
    Version,
    Tag,
    Changelog,
    Issue)
from allmychanges.validators import URLValidator


class URLField(fields.URLField):
    def __init__(self, **kwargs):
        if 'validators' not in kwargs:
            kwargs['validators'] = [URLValidator()]
        super(URLField, self).__init__(**kwargs)


class JSONField(serializers.WritableField):
    """ https://github.com/tomchristie/django-rest-framework/issues/1880#issuecomment-70392048
    """
    def __init__(self, *args, **kwargs):
        # My own way of dealing with the allow_none error issue described here:
        #   https://github.com/tomchristie/django-rest-framework/issues/1809
        #   https://github.com/tomchristie/django-rest-framework/issues/1880
        kwargs.pop('allow_none', None)

        super(JSONField, self).__init__(*args, **kwargs)

    def from_native(self, value):
        if value is not None and not isinstance(value, (dict, list)):
            raise exceptions.ValidationError("Invalid JSON <{}>".format(value))

        return value

    def to_native(self, obj):
        return obj


class ModelSerializer(serializers.ModelSerializer):
    """This serializer uses custom URL serializer instead of
    standart one and should be used anywhere instead of
    rest framework's serializer.
    """
    field_mapping = serializers.ModelSerializer.field_mapping.copy()
    field_mapping[serializers.models.URLField] = URLField


class SubscriptionSerializer(ModelSerializer):
    class Meta:
        model = Subscription
        fields = (
            'email',
            'date_created',
        )


class AbsoluteUriField(serializers.Field):
    """
    Represents a link to object's web representation.
    """
    read_only = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('source', 'get_absolute_url')
        super(AbsoluteUriField, self).__init__(*args, **kwargs)

    def to_native(self, obj):
        request = self.context['request']
        return request.build_absolute_uri(obj)


class ChangelogSerializer(ModelSerializer):
    resource_uri = ResourceUriField(view_name='changelog-detail')
    absolute_uri = AbsoluteUriField()
    problem = serializers.Field(source='problem')
    updated_at = serializers.Field(source='updated_at')
    next_update_at = serializers.Field(source='next_update_at')
    latest_version = serializers.Field(source='latest_version')
    downloader = serializers.WritableField(required=False)
    downloader_settings = JSONField(required=False)
    downloaders = JSONField(required=False)

    class Meta:
        model = Changelog
        fields = (
            'resource_uri',
            'absolute_uri',
            'namespace',
            'name',
            'description',
            'source',
            'icon',
            'created_at',
            'updated_at',
            'next_update_at',
            'problem',
            'latest_version',
            'ignore_list',
            'search_list',
            'xslt',
            'downloader',
            'downloader_settings',
            'downloaders',
        )

    def validate(self, attrs):
        # we need to check this to ensure that correct downloader was
        # choosen by user at the "Tune&Preview" stage.
        if attrs.get('source') and not attrs.get('downloader'):
            raise ValidationError('Downloader is required when source field is not empty')
        return attrs


class PreviewSerializer(ModelSerializer):
    resource_uri = ResourceUriField(view_name='preview-detail')
    downloader_settings = JSONField()
    downloaders = JSONField()

    class Meta:
        model = Preview
        fields = (
            'downloader',
            'downloader_settings',
            'downloaders',
            'resource_uri',
            'status',
            'processing_status',
            'log',
            'problem',
        )


class VersionSerializer(ModelSerializer):
    class Meta:
        model = Version


class TagSerializer(ModelSerializer):
    version_number = serializers.Field(source='version.number')
    changelog = serializers.Field(source='version.changelog.id')

    class Meta:
        model = Tag
        fields = ('name',
                  'version_number',
                  'changelog')


class IssueSerializer(ModelSerializer):
    class Meta:
        model = Issue
