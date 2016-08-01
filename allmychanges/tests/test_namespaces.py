# coding: utf-8

from allmychanges.models import Changelog
from hamcrest import (
    assert_that,
    equal_to,
    contains,
)

_num_created = [0]

def create(namespace):
    idx = _num_created[0]
    _num_created[0] += 1

    return Changelog.objects.create(
        namespace=namespace,
        name='project-{0}'.format(idx),
        source='test'
    )


def create_with_exactly_this_namespace(namespace):
    # we need this because standart save/update
    # methods change case to most used
    changelog = create(namespace)
    Changelog.objects.filter(id=changelog.id).update(namespace=namespace)


def get_all_namespaces():
    return list(Changelog.objects.values_list('namespace', flat=True).distinct())


def test_namespace_name_should_keep_case_of_the_first_entry():
    # Checking if first project was created with namespace "C",
    # all next projects will have namespace "C" even if user
    # specified "c"

    create('C')
    create('c')
    create('c')

    namespaces = get_all_namespaces()
    assert_that(
        namespaces,
        equal_to(['C'])
    )


def test_data_migration_for_namespace_case():
    # after the constraint was introduced, we need
    # to fix namespace's case for some project
    # Algorithm is simple - just choose case which
    # is used in more projects.

    create_with_exactly_this_namespace('clojure')
    create_with_exactly_this_namespace('clojure')
    create_with_exactly_this_namespace('Clojure')

    create_with_exactly_this_namespace('C')
    create_with_exactly_this_namespace('C')
    create_with_exactly_this_namespace('c')

    create_with_exactly_this_namespace('python')
    create_with_exactly_this_namespace('python')
    create_with_exactly_this_namespace('Python')
    create_with_exactly_this_namespace('Python')

    namespaces = get_all_namespaces()
    namespaces.sort()

    # ensure, there are different namespaces in the database
    assert_that(
        namespaces,
        contains('C', 'Clojure', 'Python', 'c', 'clojure', 'python')
    )

    Changelog.normalize_namespaces()

    namespaces = get_all_namespaces()
    namespaces.sort()

    # ensure, there are different namespaces in the database
    assert_that(
        namespaces,
        contains('C', 'clojure', 'python')
    )
