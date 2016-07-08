# -*- coding: utf-8 -*-
import re
import random

from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count
from django import forms
from django.contrib import messages
from django.utils.encoding import force_str
from itertools import islice
from urllib import urlencode
from collections import defaultdict

from rest_framework import views, viewsets, mixins, permissions
from rest_framework.exceptions import ParseError
from rest_framework_extensions.mixins import DetailSerializerMixin
from rest_framework_extensions.decorators import action
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from allmychanges.downloaders.utils import normalize_url
from allmychanges.models import (Subscription,
                                 Preview,
                                 Issue,
                                 Version,
                                 AutocompleteData,
                                 Changelog,
                                 UserHistoryLog)
from allmychanges import chat
from allmychanges.api.serializers import (
    SubscriptionSerializer,
    PreviewSerializer,
    ChangelogSerializer,
    IssueSerializer,
    VersionSerializer,
    TagSerializer)

from allmychanges.utils import (
    count,
    parse_ints,
    join_ints,
    reverse,
    project_slack_name,
    user_slack_name,
    update_fields)
from allmychanges.source_guesser import guess_source


from rest_framework.exceptions import APIException


# http://www.django-rest-framework.org/api-guide/exceptions
class AlreadyExists(APIException):
    status_code = 400
    default_detail = 'Object already exists'


class AccessDenied(APIException):
    status_code = 403
    default_detail = 'You are not allowed to perform this action'


TAG_NAME_REGEX = ur'^[a-z][a-z0-9-.]{,38}[a-z0-9]$'
TAG_NAME_ERROR_MESSAGES = dict(
    required='This field is required',
    invalid=('Tag names should correspond to this '
            'regular expression: "{}"').format(
                TAG_NAME_REGEX))


class TagForm(forms.Form):
    name = forms.RegexField(TAG_NAME_REGEX,
                            error_messages=TAG_NAME_ERROR_MESSAGES)
    version = forms.CharField()


class UntagForm(forms.Form):
    name = forms.RegexField(TAG_NAME_REGEX,
                            error_messages=TAG_NAME_ERROR_MESSAGES)


class HandleExceptionMixin(object):
    def dispatch(self, *args, **kwargs):
        with transaction.atomic():
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
                    results.append(dict(
                        type='namespace',
                        namespace=namespace,
                        url=reverse('category',
                                    category=namespace)))


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
                            pk=changelog.pk))
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
                    results.append(
                        dict(type='namespace',
                             namespace=namespace,
                             url=reverse('category',
                                         category=namespace)))


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
                            pk=changelog.pk))
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
                    results.append(
                        dict(type='namespace',
                             namespace=namespace,
                             url=reverse('category',
                                         category=namespace)))


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
    """This view returns next changelog item for
    landing page.
    """
    def list(self, request, *args, **kwargs):
        def process_versions(versions):
            return [{'id': v.id,
                     'number': v.number,
                     'date': v.date or v.discovered_at.date(),
                     'text': v.processed_text}
                    for v in versions]

        limit = int(request.GET.get('limit', '3'))
        versions_limit = int(request.GET.get('versions_limit', '3'))
        user = request.user

        if user.is_authenticated():
            tracked_changelogs = set(user.changelogs.all().values_list('id', flat=True))
            skipped_changelogs = set(user.skips_changelogs.all().values_list('id', flat=True))
        else:
            tracked_changelogs = set(parse_ints(request.COOKIES.get('tracked-changelogs', '')))
            skipped_changelogs = set(parse_ints(request.COOKIES.get('skipped-changelogs', '')))

        skip = tracked_changelogs | skipped_changelogs
        tracked_namespaces = Changelog.objects.exclude(name=None).filter(pk__in=tracked_changelogs).values_list('namespace', flat=True)
        skipped_namespaces = Changelog.objects.exclude(name=None).filter(pk__in=skipped_changelogs).values_list('namespace', flat=True)
        scores = defaultdict(int)
        for ns in tracked_namespaces:
            scores[ns] += 1
        for ns in skipped_namespaces:
            scores[ns] -= 1

        changelog_ids = list(Changelog.objects.good() \
                                      .exclude(name='allmychanges') \
                                      .annotate(num_trackers=Count('trackers')) \
                                      .values_list('id', 'namespace', 'num_trackers'))
        changelog_ids.sort(key=lambda item: item[2] + scores.get(item[1], 0),
                           reverse=True)
        changelog_ids = (item for item in changelog_ids
                         if item[0] not in skip)

        changelog_ids = [item[0]
                         for item in islice(changelog_ids, limit * 3)]
        # adding a little of chaos
        if len(changelog_ids) > limit:
            changelog_ids = random.sample(changelog_ids, limit)

        changelogs = Changelog.objects.filter(pk__in=changelog_ids)

        return Response({'results': [{'id': ch.id,
                                      'name': ch.name,
                                      'namespace': ch.namespace,
                                      'description': ch.description,
                                      'versions': process_versions(ch.versions.all()[:versions_limit])}
                                     for ch in changelogs]})


class AuthenticationRequired(object):
    def has_permission(self, request, view, obj=None):
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated()


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
        # TODO: decide if we want to show all changelogs to
        #       not authenticated users
        if self.request.GET.get('tracked', 'False') == 'True':
            if self.request.user.is_authenticated():
                return self.request.user.changelogs.all()
            else:
                return []
        else:
            queryset = super(ChangelogViewSet, self).get_queryset(*args, **kwargs)
            namespace = self.request.GET.get('namespace')
            name = self.request.GET.get('name')
            source = self.request.GET.get('source')
            id__in = self.request.GET.get('id__in')

            if namespace is not None:
                queryset = queryset.filter(namespace=namespace)
            if name is not None:
                queryset = queryset.filter(name=name)
            if source is not None:
                normalized_source, _, _ = normalize_url(source,
                                                        for_checkout=False)
                queryset = queryset.filter(source=normalized_source)

            if id__in is not None:
                ids = id__in.split(',')
                ids = filter(None, ids)
                ids = map(int, ids)
                queryset = queryset.filter(id__in=ids)

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

        if self.object.versions.count() == 0:
            # try to move preview's versions

            preview = list(self.object.previews.filter(
                light_user=self.request.light_user).order_by('-id')[:1])
            if preview:
                preview = preview[0]
                for version in preview.versions.all():
                    version.preview = None
                    version.changelog = self.object
                    version.save()
                    version.associate_with_free_tags()

        result = self.object.add_to_moderators(self.request.user,
                                               self.request.light_user)
        if result:
            messages.info(self.request._request,
                          'Congratulations, you\'ve become a moderator of this '
                          'changelog. Now you have rights to edit and to care '
                          'about this changelog in future.')
        if result == 'light':
            messages.warning(self.request._request,
                             'Because you are not logged in, we\'ll remember '
                             'that you are a moderator for 24 hour. To make '
                             'this permanent, please, login or sign up as soon '
                             'as possible.')

        # after changelog settings were updated
        # most probably we want to update it's versions too
        self.object.resume()

        if self.request.method == 'PUT':
            UserHistoryLog.write(self.request.user,
                                 self.request.light_user,
                                 'package-edit',
                                 u'User edited changelog:{0}'.format(self.object.pk))
        return response

    @detail_route(methods=['post'], permission_classes=[])
    def track(self, request, pk=None):
        user = self.request.user
        changelog = Changelog.objects.get(pk=pk)
        response = Response({'result': 'ok'})

        if user.is_authenticated():
            user.track(changelog)
            chat.send(('Project {project} '
                       'was tracked by {user}.').format(
                           project=project_slack_name(changelog),
                           user=user_slack_name(user)))
        else:
            action_description = 'Anonymous user tracked changelog:{0}'.format(changelog.id)
            UserHistoryLog.write(None, self.request.light_user, 'track', action_description)

            tracked_changelogs = set(parse_ints(request.COOKIES.get('tracked-changelogs', '')))
            tracked_changelogs.add(pk)
            response.set_cookie('tracked-changelogs', join_ints(tracked_changelogs))
            chat.send(('Project {project} '
                       'was tracked by {light_user}.').format(
                           project=project_slack_name(changelog),
                           light_user=request.light_user))
        return response

    @detail_route(methods=['post'], permission_classes=[])
    def untrack(self, request, pk=None):
        user = self.request.user
        changelog = Changelog.objects.get(pk=pk)
        response = Response({'result': 'ok'})

        if user.is_authenticated():
            user.untrack(changelog)
            chat.send(('Project {project} was untracked by {user}.').format(
                project=project_slack_name(changelog),
                user=user_slack_name(user)))
        else:
            action_description = 'Anonymous user untracked changelog:{0}'.format(changelog.id)
            UserHistoryLog.write(None, self.request.light_user, 'untrack', action_description)

            tracked_changelogs = set(parse_ints(request.COOKIES.get('tracked-changelogs', '')))
            tracked_changelogs.remove(pk)
            response.set_cookie('tracked-changelogs', join_ints(tracked_changelogs))

            chat.send(('Project {project} was untracked by {light_user}.').format(
                project=project_slack_name(changelog),
                light_user=request.light_user))
        return response


    @detail_route(methods=['post'], permission_classes=[])
    def skip(self, request, pk=None):
        """Saves user's intent to not recommend him that package anymore.
        """
        user = self.request.user
        changelog = Changelog.objects.get(pk=pk)
        response = Response({'result': 'ok'})

        if user.is_authenticated():
            user.skip(changelog)
            chat.send(('Project {project} was skipped by {user}.').format(
                project=project_slack_name(changelog),
                user=user_slack_name(user)))
        else:
            action_description = 'Anonymous user skipped changelog:{0}'.format(changelog.id)
            UserHistoryLog.write(None, self.request.light_user, 'skip', action_description)

            skipped_changelogs = set(parse_ints(request.COOKIES.get('skipped-changelogs', '')))
            skipped_changelogs.add(pk)
            response.set_cookie('skipped-changelogs', join_ints(skipped_changelogs))

            chat.send(('Project {project} was skipped by {light_user}.').format(
                project=project_slack_name(changelog),
                light_user=request.light_user))
        return response


    @detail_route(methods=['post'], permission_classes=[AuthenticationRequired])
    def tag(self, request, pk=None):
        form = TagForm(request.DATA)
        if not form.is_valid():
            return Response({'errors': form.errors},
                            content_type='application/json',
                            status=400)

        name = form.cleaned_data['name']
        version_number = form.cleaned_data['version']
        changelog = self.get_object()
        status = changelog.set_tag(request.user, name, version_number)
        if status == 'created':
            status_code = 201
        else:
            status_code = 200

        return Response({'result': status},
                        status=status_code,
                        content_type='application/json')

    @detail_route(methods=['post'], permission_classes=[AuthenticationRequired])
    def untag(self, request, pk=None):
        form = UntagForm(request.DATA)
        if not form.is_valid():
            return Response({'errors': form.errors},
                            content_type='application/json',
                            status=400)

        name = form.cleaned_data['name']
        changelog = self.get_object()
        changelog.remove_tag(request.user, name)
        return Response(status=204)

    @detail_route(
        methods=['post'],
        permission_classes=[],
        # этот параметр поддерживается начиная с 3.0.3 версии
        # https://allmychanges.com/p/python/django-rest-framework/#3.0.3
        # url_path='add-to-moderators'
    )
    def add_to_moderators(self, request, pk=None):
        user = self.request.user

        if not user.is_authenticated():
            return Response(
                {'errors': 'Only authenticated user can become a moderator'},
                status=403
            )
        changelog = self.get_object()
        changelog.add_to_moderators(
            self.request.user,
            self.request.light_user
        )
        return Response({'result': 'ok'})

    @detail_route(
        methods=['post'],
        permission_classes=[],
        # этот параметр поддерживается начиная с 3.0.3 версии
        # https://allmychanges.com/p/python/django-rest-framework/#3.0.3
        # url_path='remove-from-moderators'
    )
    def remove_from_moderators(self, request, pk=None):
        user = self.request.user

        if not user.is_authenticated():
            return Response(
                {'errors': 'Only authenticated user can become a moderator'},
                status=403
            )
        changelog = self.get_object()
        changelog.remove_from_moderators(
            self.request.user,
            self.request.light_user
        )
        return Response({'result': 'ok'})



class PreviewViewSet(HandleExceptionMixin,
                     DetailSerializerMixin,
                     viewsets.ModelViewSet):
    serializer_class = PreviewSerializer
    serializer_detail_class = PreviewSerializer
    model = Preview

    def partial_update(self, *args, **kwargs):
        super(PreviewViewSet, self).partial_update(*args, **kwargs)

        data = self.request.DATA

        fields_which_can_be_updated = (
            'source',
            'downloader',
            'downloader_settings',
            'search_list',
            'ignore_list',
            'xslt')

        updated_fields = {
            key: value
            for key, value in data.items()
            if key in fields_which_can_be_updated}

        if updated_fields:
            update_fields(self.object,
                          log=[],
                          **updated_fields)
            self.object.schedule_update()

        return Response({'result': 'scheduled'})



# это пока нигде не используется, надо дорабатывать
# и возможно переносить ручку в changelog/:id/versions

class VersionViewSet(HandleExceptionMixin,
                     DetailSerializerMixin,
                     viewsets.ModelViewSet):
    serializer_class = VersionSerializer
    serializer_detail_class = VersionSerializer
    paginate_by = 10


    def get_queryset(self, *args, **kwargs):
        params = {
            key: self.request.GET[key]
            for key in ('changelog__namespace',
                        'changelog__name',
                        'number')
            if key in self.request.GET}
        return Version.objects.filter(**params)



class TagViewSet(HandleExceptionMixin,
                 DetailSerializerMixin,
                 viewsets.ModelViewSet):
    serializer_class = TagSerializer
    serializer_detail_class = TagSerializer
    permission_classes = [AuthenticationRequired]
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        queryset = self.request.user.tags.all()

        if 'project_id' in self.request.GET:
            queryset = queryset.filter(
                version__changelog__id=self.request.GET['project_id'])

        if 'version_id' in self.request.GET:
            queryset = queryset.filter(
                version__id=self.request.GET['version_id'])

        return queryset


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

        if namespace and name:
            try:
                already_taken = Changelog.objects \
                    .filter(namespace=namespace, name=name) \
                    .exclude(pk=changelog_id).count()

                if already_taken:
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


class UserView(views.APIView):
    """Returns information about current user.

    For now, it is only his username.

    If user is not authenticated, then it returns 401 UNAUTHORIZED
    """
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            data = dict(
                username=request.user.username,
            )
            return Response(data)
        else:
            data = dict(
                message='Requires authentication',
            )
            return Response(data, 401)



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
            if changelog:
                history_message = u'Created issue for <changelog:{0}>'.format(
                    changelog.id)
                chat_message = (
                    u'New issue was created for '
                    u'<https://allmychanges.com{issue_url}|'
                    u'{namespace}/{name}>.').format(
                        issue_url=reverse('issue-detail', pk=obj.id),
                        namespace=changelog.namespace,
                        name=changelog.name)
            else:
                history_message = u'Feedback was given at page "{0}"'.format(obj.page)
                chat_message = (
                    u'Feedback was given for page '
                    u'<https://allmychanges.com{page}|{page}> '
                    u'<https://allmychanges.com{issue_url}|#{pk}>.').format(
                        issue_url=reverse('issue-detail',
                                          pk=obj.id),
                        page=obj.page)

            UserHistoryLog.write(
                self.request.user,
                self.request.light_user,
                'create-issue',
                history_message)
            chat.send(chat_message)

    @action()
    def resolve(self, request, pk=None):
        user = self.request.user
        issue = Issue.objects.get(pk=pk)

        if issue.editable_by(user, self.request.light_user):
            issue.resolve(user)
            return Response({'result': 'ok'})
        raise AccessDenied()
