# -*- coding: utf-8 -*-
import re

from django.utils import timezone
from django.db.models import Max
from django import forms
from django.contrib import messages
from itertools import islice

from rest_framework import viewsets, mixins, views, permissions
from rest_framework.exceptions import ParseError
from rest_framework_extensions.mixins import DetailSerializerMixin
from rest_framework_extensions.decorators import action
from rest_framework.response import Response

from allmychanges.models import (Repo, Subscription, Package,
                                 Version,
                                 Changelog, UserHistoryLog)

from allmychanges.api.serializers import (
    RepoSerializer,
    RepoDetailSerializer,
    CreateChangelogSerializer,
    SubscriptionSerializer,
    ChangelogSerializer,
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


class RepoViewSet(HandleExceptionMixin,
                  DetailSerializerMixin,
                  viewsets.ReadOnlyModelViewSet):
    queryset = Repo.objects.all()
    serializer_class = RepoSerializer
    serializer_detail_class = RepoDetailSerializer
    queryset_detail = queryset.prefetch_related('versions__items__changes')

    @action(is_for_list=True, endpoint='create-changelog')
    def create_changelog(self, request, *args, **kwargs):

        serializer = CreateChangelogSerializer(data=request.DATA)
        if serializer.is_valid():
            count('api.create.changelog')
            repo = Repo.start_changelog_processing_for_url(
                url=serializer.data['url'])

            return Response(data={'id': repo.id})
        else:
            raise ParseError(detail=serializer.errors)


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


# class PackageViewSet(HandleExceptionMixin,
#                      DetailSerializerMixin,
#                      viewsets.ModelViewSet):
#     serializer_class = PackageSerializer
#     serializer_detail_class = PackageSerializer
#     paginate_by = None


#     def get_queryset(self, *args, **kwargs):
#         return self.request.user.packages.all()

#     def pre_save(self, obj):
#         obj.user = self.request.user
#         now = timezone.now()

#         if self.request.method == 'POST' and \
#            self.request.user.packages.filter(
#                namespace=obj.namespace,
#                name=obj.name).count() > 0:
#             raise AlreadyExists('Package {0}/{1} already exists'.format(
#                 obj.namespace, obj.name))

#         obj.next_update_at = now
#         if obj.created_at is None:
#             obj.created_at = now

#         obj.source, _, _ = normalize_url(obj.source, for_checkout=False)
#         return super(PackageViewSet, self).pre_save(obj)

#     def post_save(self, obj, *args, **kwargs):
#         response = super(PackageViewSet, self).post_save(obj, *args, **kwargs)
#         if self.action in ('create', 'update'):
#             update_changelog_task.delay(obj.changelog.source)
#         return response


class AutocompleteNamespaceView(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        queryset = Package.objects.filter(namespace__startswith=request.GET.get('q'))
        namespaces = list(queryset.values_list('namespace', flat=True).distinct())
        namespaces.sort()
        return Response({'results': [{'name': namespace}
                                     for namespace in namespaces]})


class AutocompletePackageNameView(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        filter_args = dict(name__startswith=request.GET.get('q'))
        queryset = Package.objects.filter(**filter_args)
        this_users_packages = request.user.packages.filter(**filter_args).values_list('name', flat=True)
        queryset = queryset.exclude(name__in=this_users_packages)
        names = list(queryset.values_list('name', flat=True).distinct())
        names.sort()
        return Response({'results': [{'name': name}
                                     for name in names]})


class SearchAutocompleteView(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        q = request.GET.get('q', '')
        splitted = re.split(r'[ /]', q, 1)
        if len(splitted) == 2:
            namespace, name = splitted
            urls = list(Changelog.objects.filter(namespace=namespace,
                                                 name__startswith=name)
                        .values_list('source', flat=True)
                        .distinct())
        else:
            namespace, name = None, q
            urls = list(Changelog.objects.filter(namespace__startswith=q)
                        .values_list('namespace', flat=True)
                        .distinct())
            urls += list(Changelog.objects.filter(name__startswith=q)
                        .values_list('source', flat=True)
                        .distinct())

        guessed_urls = guess_source(namespace, name)

        # we need this instead of sets,
        # to ensure, that urls from database
        # will retain their order
        for url in guessed_urls:
            if url not in urls:
                urls.append(url)

        return Response({'results': [{'name': url}
                                     for url in urls]})


class LandingPackageSuggestView(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        def process_versions(versions):
            return [{'number': v.number,
                     'date': v.date or v.discovered_at.date()}
                    for v in versions]

        tracked = parse_ints(request.GET.get('tracked', ''))
        ignored = parse_ints(request.GET.get('ignored', ''))
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
        changelogs = islice((ch for ch in changelogs
                            if ch.versions.filter(code_version='v2').count() > 0),
                            3)

        return Response({'results': [{'id': ch.id,
                                      'name': ch.name,
                                      'namespace': ch.namespace,
                                      'versions': process_versions(ch.versions.filter(code_version='v2')[:3])}
                                     for ch in changelogs]})


class OnlyModeratorCouldModify(object):
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
    permission_classes = [OnlyModeratorCouldModify]
    paginate_by = None
    model = Changelog

    def get_queryset(self, *args, **kwargs):
        if self.request.GET.get('tracked', 'False') == 'True':
            return self.request.user.changelogs.all()
        else:
            return super(ChangelogViewSet, self).get_queryset(*args, **kwargs)

    def update(self, *args, **kwargs):
        response = super(ChangelogViewSet, self).update(*args, **kwargs)
        result = self.object.add_to_moderators(self.request.user,
                                               self.request.light_user)
        if result:
            messages.info(self.request,
                          'Congratulations, you\'ve become a moderator of this changelog. Now you have rights to edit and care about this changelog in future.')
        if result == 'light':
            messages.warning(self.request,
                             'Because you are not logged in, we\'ll remember that you are a moderator for 24 hour. To make this permanent, please, login or sign up as soon as possible.')

        return response

    @action()
    def track(self, request, pk=None):
        user = self.request.user
        changelog = Changelog.objects.get(pk=pk)
        response = Response({'result': 'ok'})

        if user.is_authenticated():
            user.track(changelog)
        else:
            tracked_changelogs = set(parse_ints(request.COOKIES.get('tracked-changelogs', '')))
            tracked_changelogs.add(pk)
            response.set_cookie('tracked-changelogs', join_ints(tracked_changelogs))
        return response

    @action()
    def untrack(self, request, pk=None):
        user = self.request.user
        if user.is_authenticated():
            changelog = Changelog.objects.get(pk=pk)
            user.untrack(changelog)
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
                            views.APIView):
    def get(self, *args, **kwargs):
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
