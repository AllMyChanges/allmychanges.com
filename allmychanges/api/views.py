# -*- coding: utf-8 -*-
import re

from django.utils import timezone
from django.db.models import Max, Q
from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.encoding import force_str
from itertools import islice
from twiggy_goodies.threading import log
from urllib import urlencode

from rest_framework import viewsets, mixins, permissions
from rest_framework.exceptions import ParseError
from rest_framework_extensions.mixins import DetailSerializerMixin
from rest_framework_extensions.decorators import action
from rest_framework.response import Response

from allmychanges.downloader import normalize_url
from allmychanges.models import (Subscription,
                                 Issue,
                                 Version,
                                 AutocompleteData,
                                 Changelog, UserHistoryLog)
from allmychanges import chat
from allmychanges.api.serializers import (
    SubscriptionSerializer,
    ChangelogSerializer,
    IssueSerializer,
    VersionSerializer,
)
from allmychanges.utils import (count,
                                parse_ints,
                                join_ints)
from allmychanges.source_guesser import guess_source


from rest_framework.exceptions import APIException


# http://www.django-rest-framework.org/api-guide/exceptions
class AlreadyExists(APIException):
    status_code = 400
    default_detail = 'Object already exists'


class AccessDenied(APIException):
    status_code = 403
    default_detail = 'You are not allowed to perform this action'


from django.db import transaction


class HandleExceptionMixin(object):
    @transaction.atomic()
    def dispatch(self, *args, **kwargs):
        return super(HandleExceptionMixin, self).dispatch(*args, **kwargs)

    def handle_exception(self, exc):
        count('api.exception')
        if isinstance(exc, ParseError):
            return Response(data={u'error_messages': exc.detail},
                            status=400,
                            exception=exc)
        return super(HandleExceptionMixin, self).handle_exception(exc=exc)


class SubscriptionViewSet(HandleExceptionMixin,
                          mixins.CreateModelMixin,
                          viewsets.GenericViewSet):
    model = Subscription
    serializer_class = SubscriptionSerializer

    def create(self, request, *args, **kwargs):
        request.DATA['date_created'] = timezone.now()
        count('api.create.subscription')
        return super(SubscriptionViewSet, self) \
            .create(request, *args, **kwargs)


class AutocompleteNamespaceView(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        queryset = Changelog.objects.filter(namespace__startswith=request.GET.get('q'))
        namespaces = list(queryset.values_list('namespace', flat=True).distinct())
        namespaces.sort()
        return Response({'results': [{'name': namespace}
                                     for namespace in namespaces]})


class AutocompletePackageNameView(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        filter_args = dict(name__startswith=request.GET.get('q'))
        queryset = Changelog.objects.filter(**filter_args)
        this_users_packages = request.user.changelogs.filter(**filter_args).values_list('name', flat=True)
        queryset = queryset.exclude(name__in=this_users_packages)
        names = list(queryset.values_list('name', flat=True).distinct())
        names.sort()
        return Response({'results': [{'name': name}
                                     for name in names]})


# TODO: remove some day
class SearchAutocomplete1View(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        q = request.GET.get('q', '')
        splitted = re.split(r'[ /]', q, 1)
        results = []
        sources = set()

        def add_changelogs(changelogs):
            for changelog in changelogs:
                sources.add(changelog.source)
                results.append(dict(type='package',
                                    namespace=changelog.namespace,
                                    name=changelog.name,
                                    source=changelog.source,
                                    url=changelog.get_absolute_url()))


        if len(splitted) == 2:
            namespace, name = splitted
            add_changelogs(Changelog.objects.filter(namespace=namespace,
                                                    name__icontains=name).distinct())
        else:
            namespaces = Changelog.objects.exclude(namespace=None).exclude(name=None).values_list('namespace', flat=True).distinct()
            for namespace in namespaces:
                if q in namespace:
                    results.append(dict(type='namespace',
                                         namespace=namespace,
                                         url='/catalogue/#' + namespace))


            namespace, name = None, q
            add_changelogs(Changelog.objects.filter(name__icontains=q)
                        .distinct())

        guessed_urls = guess_source(namespace, name)

        # we need this instead of sets,
        # to ensure, that urls from database
        # will retain their order
        for url in guessed_urls:
            if url not in sources:
                results.append(dict(type='add-new',
                                    source=url,
                                    url='/p/new/?' + urlencode(dict(url=url))))

        return Response({'results': results})


# TODO: remove some day
class SearchAutocomplete2View(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        name = request.GET.get('q', '')
        namespace = request.GET.get('namespace') # optional

        results = []
        sources = set()

        def add_changelogs(changelogs):
            for changelog in changelogs:
                sources.add(changelog.source)
                resource_uri = request.build_absolute_uri(
                    reverse('changelog-detail',
                            kwargs=dict(pk=changelog.pk)))
                results.append(dict(type='package',
                                    namespace=changelog.namespace,
                                    name=changelog.name,
                                    source=changelog.source,
                                    resource_uri=resource_uri,
                                    icon=changelog.icon,
                                    url=changelog.get_absolute_url()))

        if not namespace:
            splitted = re.split(r'[ /]', name, 1)
            if len(splitted) == 2:
                namespace, name = splitted

        if namespace:
            add_changelogs(Changelog.objects.filter(namespace=namespace,
                                                    name__icontains=name).distinct())
        else:
            namespaces = Changelog.objects.exclude(namespace=None).exclude(name=None).values_list('namespace', flat=True).distinct()
            for namespace in namespaces:
                if name in namespace:
                    results.append(dict(type='namespace',
                                         namespace=namespace,
                                         url='/catalogue/#' + namespace))


            add_changelogs(Changelog.objects.filter(name__icontains=name)
                        .distinct())

        data = AutocompleteData.objects.filter(
            words__word__istartswith=name)
        data = data.filter(origin='app-store')
        data = data.distinct()

        for item in data[:10]:
            url = item.source
            if url not in sources:
                results.append(dict(type='add-new',
                                    source=url,
                                    name=item.title,
                                    namespace='ios',
                                    icon=item.icon,
                                    url='/p/new/?' + urlencode(dict(url=url))))

        return Response({'results': results})



class SearchAutocompleteView(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        name = request.GET.get('q', '').strip().lower()
        if len(name) < 3:
            return Response({'results': []})

        namespace = request.GET.get('namespace') # optional

        results = []
        sources = set()

        def add_changelogs(changelogs):
            for changelog in changelogs:
                sources.add(changelog.source)
                resource_uri = request.build_absolute_uri(
                    reverse('changelog-detail',
                            kwargs=dict(pk=changelog.pk)))
                results.append(dict(type='package',
                                    namespace=changelog.namespace,
                                    name=changelog.name,
                                    description=changelog.description,
                                    source=changelog.source,
                                    resource_uri=resource_uri,
                                    icon=changelog.icon,
                                    url=changelog.get_absolute_url()))

        if not namespace:
            splitted = re.split(r'[ /]', name, 1)
            if len(splitted) == 2:
                namespace, name = splitted

        if namespace:
            add_changelogs(Changelog.objects.filter(namespace=namespace,
                                                    name__icontains=name).distinct())
        else:
            namespaces = Changelog.objects.exclude(namespace=None).exclude(name=None).values_list('namespace', flat=True).distinct()
            for namespace in namespaces:
                if name in namespace:
                    results.append(dict(type='namespace',
                                         namespace=namespace,
                                         url='/catalogue/#' + namespace))


            add_changelogs(Changelog.objects.filter(name__icontains=name)
                        .distinct())

        query = name.replace(' ', '').lower()
        query = Q(words2__word__istartswith=query)
        # над этой частью надо подумать, ибо так не работает
        # надо как-то ранжировать результаты автокомплита
        # может попробовать засунуть их в elastic search
        # if ' ' in name:
        #     names = filter(None, name.split(' '))
        #     query |= reduce(operator.__and__,
        #                     (Q(words2__word__startswith=item)
        #                      for item in names))

        data = AutocompleteData.objects.filter(query)

        if namespace == 'ios':
            data = data.filter(origin='app-store')

        data = data.order_by('-score')
        data = data.distinct()
        data = list(data[:10])


        # sort results, so that thouse which title
        # starts from the query go first and shorter title go first
        def cmp(left, right):
            left_title = left.title.lower()
            if left_title.startswith(name):
                right_title = right.title.lower()
                if right_title.startswith(name):
                    if len(right_title) < len(left_title):
                        return -1
                return 1
            return -1

#        data.sort(cmp=cmp, reverse=True)

        for item in data:
            url = item.source
            if url not in sources:
                params = dict(
                    url=url,
                    name=item.title.split(' by ')[0],
                    namespace='ios',
                    description=item.description)
                params = {key: force_str(value)
                          for key, value in params.items()}
                params = urlencode(params)
                results.append(dict(type='add-new',
                                    source=url,
                                    name=item.title,
                                    namespace='ios',
                                    description=item.description,
                                    icon=item.icon,
                                    url='/p/new/?' + params))

        return Response({'results': results})



class LandingPackageSuggestView(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        def process_versions(versions):
            return [{'id': v.id,
                     'number': v.number,
                     'date': v.date or v.discovered_at.date()}
                    for v in versions]

        tracked = parse_ints(request.GET.get('tracked', ''))
        ignored = parse_ints(request.GET.get('ignored', ''))
        limit = int(request.GET.get('limit', '3'))
        versions_limit = int(request.GET.get('versions_limit', '3'))
        skip = parse_ints(request.GET.get('skip', ''))
        skip += tracked + ignored

        track_id = request.GET.get('track_id')
        ignore_id = request.GET.get('ignore_id')

        if track_id:
            UserHistoryLog.write(request.user, request.light_user,
                'landing-track',
                'User has tracked changelog:{0}'.format(track_id))

        if ignore_id:
            UserHistoryLog.write(request.user, request.light_user,
                'landing-ignore',
                'User has ignored changelog:{0}'.format(ignore_id))

        changelogs = Changelog.objects.exclude(name=None).exclude(pk__in=skip).annotate(latest_date=Max('versions__discovered_at')).order_by('-latest_date')

        changelogs = (ch for ch in changelogs
                      if ch.versions.filter(code_version='v2').count() > 0)

        # we won't suggest changlogs which are already tracked
        if self.request.user.is_authenticated():
            tracked_changelogs = set(self.request.user.changelogs.values_list('id', flat=True))
            changelogs = (ch for ch in changelogs
                          if ch.pk not in tracked_changelogs)

        changelogs = islice(changelogs, limit)

        return Response({'results': [{'id': ch.id,
                                      'name': ch.name,
                                      'namespace': ch.namespace,
                                      'versions': process_versions(ch.versions.filter(code_version='v2')[:versions_limit])}
                                     for ch in changelogs]})


class OnlyOwnerCouldModify(object):
    def has_permission(self, request, view, obj=None):
        return True

    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS:
            return obj.editable_by(request.user,
                                   request.light_user)
        return True


class ChangelogViewSet(HandleExceptionMixin,
                       DetailSerializerMixin,
                       viewsets.ModelViewSet):
    serializer_class = ChangelogSerializer
    serializer_detail_class = ChangelogSerializer
    permission_classes = [OnlyOwnerCouldModify]
    paginate_by = None
    model = Changelog

    def get_queryset(self, *args, **kwargs):
        if self.request.GET.get('tracked', 'False') == 'True':
            return self.request.user.changelogs.all()
        else:
            queryset = super(ChangelogViewSet, self).get_queryset(*args, **kwargs)
            namespace = self.request.GET.get('namespace')
            name = self.request.GET.get('name')
            source = self.request.GET.get('source')

            if namespace is not None:
                queryset = queryset.filter(namespace=namespace)
            if name is not None:
                queryset = queryset.filter(name=name)
            if source is not None:
                normalized_source, _, _ = normalize_url(source,
                                                        for_checkout=False)
                queryset = queryset.filter(source=normalized_source)
            return queryset

    def get_object(self, *args, **kwargs):
        obj = super(ChangelogViewSet, self).get_object(*args, **kwargs)
        # saving to be able to check in `update` if the source was changed
        self.original_source = obj.source
        return obj

    def create(self, *args, **kwargs):
        response = super(ChangelogViewSet, self).create(
            *args, **kwargs)
        # put changelog into the queue right
        # away
        if getattr(self, 'object', None):
            self.object.schedule_update()
        return response

    def update(self, *args, **kwargs):
        response = super(ChangelogViewSet, self).update(*args, **kwargs)

        if self.original_source != self.object.source:
            self.object.downloader = None
            self.object.save(update_fields=('downloader',))

        if self.object.versions.count() == 0:
            # try to move preview's versions

            preview = list(self.object.previews.filter(light_user=self.request.light_user).order_by('-id')[:1])
            if preview:
                preview = preview[0]
                for version in preview.versions.all():
                    version.preview = None
                    version.changelog = self.object
                    version.save()

        result = self.object.add_to_moderators(self.request.user,
                                               self.request.light_user)
        if result:
            messages.info(self.request,
                          'Congratulations, you\'ve become a moderator of this changelog. Now you have rights to edit and to care about this changelog in future.')
        if result == 'light':
            messages.warning(self.request,
                             'Because you are not logged in, we\'ll remember that you are a moderator for 24 hour. To make this permanent, please, login or sign up as soon as possible.')


        if self.request.method == 'PUT':
            UserHistoryLog.write(self.request.user,
                                 self.request.light_user,
                                 'package-edit',
                                 u'User edited changelog:{0}'.format(self.object.pk))
        return response

    @action()
    def track(self, request, pk=None):
        user = self.request.user
        changelog = Changelog.objects.get(pk=pk)
        response = Response({'result': 'ok'})

        if user.is_authenticated():
            user.track(changelog)
            chat.send(('Package <https://allmychanges.com{url}> was tracked by {username}.').format(
                url=changelog.get_absolute_url(),
                username=user.username))
        else:
            tracked_changelogs = set(parse_ints(request.COOKIES.get('tracked-changelogs', '')))
            tracked_changelogs.add(pk)
            response.set_cookie('tracked-changelogs', join_ints(tracked_changelogs))
            chat.send(('Package <https://allmychanges.com{url}> was tracked by anonymous user.').format(
                url=changelog.get_absolute_url()))
        return response

    @action()
    def untrack(self, request, pk=None):
        user = self.request.user
        if user.is_authenticated():
            changelog = Changelog.objects.get(pk=pk)
            user.untrack(changelog)
            chat.send(('Package <https://allmychanges.com{url}> was untracked by {username}.').format(
                url=changelog.get_absolute_url(),
                username=user.username))
        else:
            chat.send(('Package <https://allmychanges.com{url}> was untracked by anonymous user.').format(
                url=changelog.get_absolute_url()))
        return Response({'result': 'ok'})



# это пока нигде не используется, надо дорабатывать
# и возможно переносить ручку в changelog/:id/versions

class VersionViewSet(HandleExceptionMixin,
                     DetailSerializerMixin,
                     viewsets.ModelViewSet):
    serializer_class = VersionSerializer
    serializer_detail_class = VersionSerializer
    paginate_by = 10


    def get_queryset(self, *args, **kwargs):
        return Version.objects.all()


_error_messages = {'required': 'Please, fill this field'}
_error_backslash = 'Field should not contain backslashes'
_error_regex = ur'^[^/]+$'


class NamespaceAndNameForm(forms.Form):
    changelog_id = forms.IntegerField(required=False)
    namespace = forms.RegexField(_error_regex,
                                 error_messages=_error_messages,
                                 error_message=_error_backslash)
    name = forms.RegexField(_error_regex,
                            error_messages=_error_messages,
                            error_message=_error_backslash)

    def clean(self):
        cleaned_data = super(NamespaceAndNameForm, self).clean()
        changelog_id = cleaned_data.get('changelog_id')
        namespace = cleaned_data.get('namespace')
        name = cleaned_data.get('name')

        try:
            changelog = Changelog.objects.get(namespace=namespace,
                                              name=name)

            if changelog.pk != changelog_id:
                self._errors['name'] = ['These namespace/name pair already taken.']
        except Changelog.DoesNotExist:
            pass

        return cleaned_data


class ValidateChangelogName(HandleExceptionMixin,
                            viewsets.ViewSet):
    def list(self, *args, **kwargs):
        form = NamespaceAndNameForm(self.request.GET)
        if form.is_valid():
            return Response({'result': 'ok'},
                            content_type='application/json')
        else:
            return Response({'errors': form.errors},
                            content_type='application/json')


class MessagesView(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        storage = messages.get_messages(request)
        msgs = [{'level': m.level,
                 'tags': m.tags,
                 'message': m.message} for m in storage]
        return Response(msgs)


class IssueViewSet(HandleExceptionMixin,
                   DetailSerializerMixin,
                   viewsets.ModelViewSet):
    serializer_detail_class = IssueSerializer
    permission_classes = [OnlyOwnerCouldModify]
    paginate_by = 20
    model = Issue

    def pre_save(self, obj):
        super(IssueViewSet, self).pre_save(obj)
        if not obj.light_user:
            obj.light_user = self.request.light_user
        if not obj.user and self.request.user.is_authenticated():
            obj.user = self.request.user

    def post_save(self, obj, created=False):
        if created:
            changelog = obj.changelog
            UserHistoryLog.write(
                self.request.user,
                self.request.light_user,
                'create-issue',
                'Created issue for <changelog:{0}>'.format(changelog.id))
            chat.send('New issue was created for <https://allmychanges.com/issues/?namespace={namespace}&name={name}|{namespace}/{name}>.'.format(
                namespace=changelog.namespace,
                name=changelog.name))

    @action()
    def resolve(self, request, pk=None):
        user = self.request.user
        issue = Issue.objects.get(pk=pk)

        if issue.editable_by(user, self.request.light_user):
            issue.resolved_at = timezone.now()
            issue.save(update_fields=('resolved_at',))
            chat.send(('Issue <https://allmychanges.com/issues/{issue_id}/|#{issue_id}> '
                       'for {namespace}/{name} was resolved by {username}.').format(
                issue_id=issue.id,
                namespace=issue.changelog.namespace,
                name=issue.changelog.name,
                username=user.username))

            if issue.type == 'auto-paused':
                changelog = issue.changelog
                with log.fields(changelog_id=changelog.id):
                    log.info('Resuming changelog updates')
                    changelog.resume()

                    chat.send('Autopaused package {namespace}/{name} was resumed {username}.'.format(
                        namespace=changelog.namespace,
                        name=changelog.name,
                        username=user.username))

            return Response({'result': 'ok'})
        raise AccessDenied()
