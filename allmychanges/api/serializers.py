# -*- coding: utf-8 -*-
from rest_framework import serializers, fields
from rest_framework_extensions.fields import ResourceUriField

from allmychanges.models import (
    Preview,
    Subscription,
    Version,
    Changelog,
    Issue)
from allmychanges.validators import URLValidator


class URLField(fields.URLField):
    def __init__(self, **kwargs):
        if 'validators' not in kwargs:
            kwargs['validators'] = [URLValidator()]
        super(URLField, self).__init__(**kwargs)


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
        )


class PreviewSerializer(ModelSerializer):
    resource_uri = ResourceUriField(view_name='preview-detail')

    class Meta:
        model = Preview
        fields = (
            'downloader',
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


class IssueSerializer(ModelSerializer):
    class Meta:
        model = Issue
