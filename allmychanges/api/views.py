# -*- coding: utf-8 -*-
from django.utils import timezone
from django.db.models import Max

from rest_framework import viewsets, mixins
from rest_framework.exceptions import ParseError
from rest_framework_extensions.mixins import DetailSerializerMixin
from rest_framework_extensions.decorators import action
from rest_framework.response import Response

from allmychanges.models import (Repo, Subscription, Package,
                                 Changelog, UserHistoryLog)
from allmychanges.tasks import update_changelog_task
from allmychanges.api.serializers import (
    RepoSerializer,
    RepoDetailSerializer,
    CreateChangelogSerializer,
    SubscriptionSerializer,
    PackageSerializer,
)
from allmychanges.utils import count, normalize_url
from allmychanges.source_guesser import guess_source


from rest_framework.exceptions import APIException


# http://www.django-rest-framework.org/api-guide/exceptions
class AlreadyExists(APIException):
    status_code = 400
    default_detail = 'Object already exists'
    

class HandleExceptionMixin(object):
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


class PackageViewSet(HandleExceptionMixin,
                     DetailSerializerMixin,
                     viewsets.ModelViewSet):
    serializer_class = PackageSerializer
    serializer_detail_class = PackageSerializer
    paginate_by = None


    def get_queryset(self, *args, **kwargs):
        return self.request.user.packages.all()

    def pre_save(self, obj):
        obj.user = self.request.user
        now = timezone.now()

        if self.request.method == 'POST' and \
           self.request.user.packages.filter(
               namespace=obj.namespace,
               name=obj.name).count() > 0:
            raise AlreadyExists('Package {0}/{1} already exists'.format(
                obj.namespace, obj.name))
        
        obj.next_update_at = now
        if obj.created_at is None:
            obj.created_at = now

        obj.source, _, _ = normalize_url(obj.source, for_checkout=False)
        return super(PackageViewSet, self).pre_save(obj)

    def post_save(self, obj, *args, **kwargs):
        response = super(PackageViewSet, self).post_save(obj, *args, **kwargs)
        if self.action in ('create', 'update'):
            update_changelog_task.delay(obj.changelog.source)
        return response
        

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


class AutocompleteSourceView(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        namespace = request.GET.get('namespace')
        name = request.GET.get('name')
        
        urls = list(Changelog.objects.filter(packages__namespace=namespace,
                                             packages__name=name) \
                    .values_list('source', flat=True) \
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

        tracked = map(int, filter(None, request.GET.get('tracked', '').split(',')))
        ignored = map(int, filter(None, request.GET.get('ignored', '').split(',')))
        skip = map(int, filter(None, request.GET.get('skip', '').split(',')))
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

        return Response({'results': [{'id': ch.id,
                                      'name': ch.name,
                                      'namespace': ch.namespace,
                                      'versions': process_versions(ch.versions.filter(code_version='v1')[:3])}
                                     for ch in changelogs[:3]]})
