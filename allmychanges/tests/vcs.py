# coding: utf-8
import datetime

from nose.tools import eq_
from asserts import sparse_check
from allmychanges.parsing.pipeline import vcs_processing_pipe
from allmychanges.vcs_extractor import (
    mark_version_bumps,
    process_vcs_message,
    _normalize_version_numbers2,
    write_vcs_versions_bin_helper,
    iterate_over_commits,
    find_fork_point,
    group_versions)


def _build_tree(tree=None, root=None):
    """
    Tree structure:
    * root (3)
    * 8 (3)
    * 7 (2)
    * 6 (2) # merge
    |\
    | * 5 (1)
    * | 4 (2)
    |/
    * 3 (1)
    * 2 (1)
    * 1 (None)

    Brackets contains discovered version number
    """
    tree = tree or {
        '9': {'version': '3', 'parents': ['8']},
        '8': {'version': '3', 'parents': ['7']},
        '7': {'version': '2', 'parents': ['6']},
        '6': {'version': '2', 'parents': ['4', '5']},
        '5': {'version': '1', 'parents': ['3']},
        '4': {'version': '2', 'parents': ['3']},
        '3': {'version': '1', 'parents': ['2']},
        '2': {'version': '1', 'parents': ['1']},
        '1': {'version': None, 'parents': []},
    }
    root = root or '9'

    for key, item in tree.items():
        item['hash'] = key
        item['message'] = 'Commit ' + key

    tree['root'] = tree[root]

    return tree


def _add_dates(tree):
    date = datetime.date
    for key in tree:
        if key != 'root':
            tree[key]['date'] = date(2014, int(key), 1)


def simplify(version):
    """Returns tuple of version-number, date, content."""
    return (version.version,
            version.date,
            version.content)
            # [re.sub(ur'<span class="changelog-item-type.*?</span>',
            #         u'',
            #         item['text'])
            #  for item in version.content[0]])

def test_extract_from_vcs():
    date = datetime.date

    tree = _build_tree()
    _add_dates(tree)

    versions = vcs_processing_pipe(tree)


    sparse_check([
        ('x.x.x',
         None,
         '<ul><li>Commit 9</li></ul>'),
        ('1',
         date(2014, 2, 1), # version 1 was released with 2nd commit
         '<ul><li>Commit 2</li>'
         '<li>Commit 1</li></ul>'),
        ('2',
          date(2014, 4, 1), # version 2 was released with 4th commit
          '<ul><li>Commit 4</li>'
          '<li>Commit 3</li></ul>'),
        ('3',
         date(2014, 8, 1), # version 3 was released with 8th commit
         '<ul><li>Commit 8</li>'
         '<li>Commit 7</li>'
         # 'Commit 6', this is a merge and it is excluded
         '<li>Commit 5</li></ul>'),
    ], map(simplify, versions))


def test_mark_version_bumps():
    tree = _build_tree()
    _add_dates(tree)
    bumps = mark_version_bumps(tree)
    eq_(['2', '4', '8'], bumps)


def test_mark_version_bumps_when_there_are_gaps():
    # in this case, oldest commit should be considered
    # as a version bump
    # Tree structure:
    # * 5 (1)
    # * 4 (1) # merge
    # |\
    # | * 3 (1)
    # * | 2 (1)
    # |/
    # * 1 (None)

    tree = _build_tree(
        tree={
            '5': {'version': '1',  'parents': ['4']},
            '4': {'version': '1',  'parents': ['2', '3']},
            '3': {'version': '1',  'parents': ['1']},
            '2': {'version': '1',  'parents': ['1']},
            '1': {'version': None, 'parents': []},
        },
        root='5')
    _add_dates(tree)
    _normalize_version_numbers2(tree)
    bumps = mark_version_bumps(tree)
    eq_(['2'], bumps)


def test_iterate_over_commits():
    # Here we use such tree
    # * 7 (2)
    # |\
    # | * 6 (1)
    # * | 5 (2)
    # * | 4 (2)
    # * | 3 (2)
    # |/
    # * 2 (1)
    # * 1 (None)

    tree = _build_tree(
        tree={
            '7': {'version': '2',  'parents': ['5', '6']},
            '6': {'version': '1',  'parents': ['2']},
            '5': {'version': '2',  'parents': ['4']},
            '4': {'version': '2',  'parents': ['3']},
            '3': {'version': '2',  'parents': ['2']},
            '2': {'version': '1',  'parents': ['1']},
            '1': {'version': None, 'parents': []},
        },
        root='7',
    )
    result = list(iterate_over_commits(tree, '5'))
    eq_(['5', '4', '3', '2', '1'], result)

    result = list(iterate_over_commits(tree, '6'))
    eq_(['6', '2', '1'], result)

    # check `upto` parameter
    result = list(iterate_over_commits(tree, '5', upto='2'))
    eq_(['5', '4', '3'], result)

    # check how merge commits are iterated
    result = list(iterate_over_commits(tree, '7'))
    eq_(['7', '5', '4', '3', '6', '2', '1'], result)


def test_find_fork_point():
    # Here we use such tree
    # * 9
    # |\
    # | * 8
    # * | 7
    # * | 6
    # * | 5
    # |/
    # * 4
    # |\
    # | * 3
    # |/
    # * 2
    # * 1

    tree = _build_tree(
        tree={
            '9': {'version': '1', 'parents': ['7', '8']},
            '8': {'version': '1', 'parents': ['4']},
            '7': {'version': '1', 'parents': ['6']},
            '6': {'version': '1', 'parents': ['5']},
            '5': {'version': '1', 'parents': ['4']},
            '4': {'version': '1', 'parents': ['2', '3']},
            '3': {'version': '1', 'parents': ['2']},
            '2': {'version': '1', 'parents': ['1']},
            '1': {'version': '1', 'parents': []},
        },
        root='9',
    )
    # this should not break because there are other merge
    # commits below '4' hash
    eq_('4', find_fork_point(tree, '6', '8'))

    # for triangle we have to return one of nodes
    eq_('2', find_fork_point(tree, '2', '3'))


def test_mark_version_bumps_outputs_bumps_in_right_order():
    # По мотивам разбирательства с обработкой python/imagesize.

    # Проблема с отсутствием 0.7.0 заключается в том, что bumps
    # формируются не в том порядке:

    # 1 0354c84 0.5.0
    # 2 151e458 0.6.0
    # 4 8bb3a11 0.7.1
    # 3 cd9c06a 0.7.0

    # А должно быть так:
    # 1 0354c84 0.5.0
    # 2 151e458 0.6.0
    # 3 cd9c06a 0.7.0
    # 4 8bb3a11 0.7.1

    #  *   68319d5 - Merge pull request #1 from xantares/py2a3 (5 weeks ago) <Yoshiki Shibukawa>
    #  |\
    #  | * 9be8ec8 - Use the same code for Python 2/3 (8 weeks ago) <Michel Zou>
    #  * | c073040 - add build status badge (5 weeks ago) <Yoshiki Shibukawa>
    #  * | 9ee206e - update readme (5 weeks ago) <Yoshiki Shibukawa>
    # 4* | 8bb3a11 - (0.7.1) update travis setting to add Python3.3 (5 weeks ago) <Yoshiki Shibukawa>
    #  * | 0750993 - add jpeg2000 test data (5 weeks ago) <Yoshiki Shibukawa>
    #  * | ce4de68 - add travis setting (5 weeks ago) <Yoshiki Shibukawa>
    #  |/
    # 3* cd9c06a - (0.7.0) catch struct.error (4 months ago) <Yoshiki Shibukawa>
    # 2* 151e458 - (0.6.0) remove fallback feature to PIL, add JPEG2000 support (4 months ago) <Yoshiki Shibukawa>
    #  * efdd3d3 - fix README (4 months ago) <Yoshiki Shibukawa>
    # 1* 0354c84 - (0.5.0) first version (4 months ago) <Yoshiki Shibukawa>

    # Версии тут проставлены так, как они менялись в setup.py,
    # что немного не соответствует тегам в гите, так как 0.7.1 тег поставлен на
    # коммит 68319d5. Но это никак не влияет на суть.

    # Неправильный порядок происходит из-за того, что обе ветки обрабатываются по
    # одному коммиту за раз из каждой. Но из-за того, что коммитов в них разное
    # количество, то по более короткой ветке алгоритм быстро доходит
    # до коммита cd9c06a и считает, что нашел версию 0.7.0 ещё до того, как
    # добрался до коммита 8bb3a11, и нашел перход на 0.7.1.

    # Поэтому для теста мы построим такую структуру:

    # * 7 (2)
    # |\
    # | * 6 (1)
    # * | 5 (2)
    # * | 4 (2)
    # * | 3 (2)
    # |/
    # * 2 (1)
    # * 1 (None)

    tree = _build_tree(
        tree={
            '7': {'version': '2',  'parents': ['5', '6']},
            '6': {'version': '1',  'parents': ['2']},
            '5': {'version': '2',  'parents': ['4']},
            '4': {'version': '2',  'parents': ['3']},
            '3': {'version': '2',  'parents': ['2']},
            '2': {'version': '1',  'parents': ['1']},
            '1': {'version': None, 'parents': []},
        },
        root='7',
    )
    _add_dates(tree)
    bumps = mark_version_bumps(tree)
    eq_(['2', '3'], bumps)


def test_mark_version_bumps_can_use_tagged_versions():
    # Проверяем, что mark_version_bumps может принимать
    # tagged_versions и они обладают преимуществом

    # Для теста мы построим такую структуру:

    # * 7 (2)
    # |\
    # | * 6 (1)
    # * | 5 (2)
    # * | 4 (2)
    # * | 3 (2)
    # |/
    # * 2 (1)
    # * 1 (None)

    tree = _build_tree(
        tree={
            '7': {'version': '2',  'parents': ['5', '6']},
            '6': {'version': '1',  'parents': ['2']},
            '5': {'version': '2',  'parents': ['4']},
            '4': {'version': '2',  'parents': ['3']},
            '3': {'version': '2',  'parents': ['2']},
            '2': {'version': '1',  'parents': ['1']},
            '1': {'version': None, 'parents': []},
        },
        root='7',
    )
    _add_dates(tree)
    tagged_versions = {
        '5': '2',
        '7': '3'
    }
    bumps = mark_version_bumps(tree, tagged_versions)
    eq_(['2', '5', '7'], bumps)


def test_group_versions():
    tree = _build_tree()
    bumps = ['2', '4', '8']
    versions = group_versions(tree, bumps)
    expected = [
        {'version': '1',
         'messages': ['Commit 2',
                      'Commit 1']},
        {'version': '2',
         'messages': ['Commit 4',
                      'Commit 3']},
        {'version': '3',
         'messages': ['Commit 8',
                      'Commit 7',
                      # 'Commit 6', this is a merge and it is excluded
                      'Commit 5']},
        {'version': 'x.x.x',
         'messages': ['Commit 9'],
         'unreleased': True}]
    sparse_check(expected, versions)


def test_group_versions_when_last_commit_is_a_version_bump():
    # in this case there shouldnt be x.x.x version
    tree = _build_tree(
        tree={
            '2': {'version': '1', 'parents': ['1']},
            '1': {'version': None, 'parents': []},
        },
        root='2')

    bumps = ['2']
    versions = group_versions(tree, bumps)
    expected = [
        {'version': '1',
         'messages': ['Commit 2',
                      'Commit 1']}]
    sparse_check(expected, versions)


def test_ignore_vcs_versions_if_there_is_only_one_unreleased_version():
    date = datetime.date
    versions = vcs_processing_pipe(
        [(None, date(2014, 1, 15), 'Initial commit'),
         (None, date(2014, 1, 15), 'Feature was added'),
         (None, date(2014, 1, 16), 'Tests were added')])
    eq_([], versions)


def test_in_vcs_messages_newlines_replaced_with_brs():
    eq_("""Some new feature was implemented.<br/>
<br/>
And new bugs are<br/>
introduced as well.""",
        process_vcs_message("""Some new feature was implemented.

And new bugs are
introduced as well."""))


def test_version_bumps_are_remove_from_commit_message():
    # https://allmychanges.com/p/python/sleekxmpp/
    eq_('', process_vcs_message('Bump to 1.3.1'))
    eq_('', process_vcs_message('bump version'))
    eq_('', process_vcs_message('Bump minor version'))
    eq_('', process_vcs_message('Bump version in prep for 1.2.0'))
    eq_('', process_vcs_message('Bump version to 1.1.10'))

    # https://allmychanges.com/p/python/pip/#6.0.6
    eq_('', process_vcs_message('Bump release for 6.0.6'))
    eq_('', process_vcs_message('Bump for release of 6.0.2'))

    # https://allmychanges.com/p/javascript/angucomplete-alt/
    eq_('', process_vcs_message('Update to v0.0.32'))
    eq_('', process_vcs_message('Update to 0.0.32'))

    # https://allmychanges.com/p/javascript/react-intl/
    eq_('', process_vcs_message('Build for 1.0.2'))

    #https://allmychanges.com/p/python/pip-autoremove/
    eq_('And some text<br/>\nto keep', process_vcs_message("""V0.8.0

And some text
to keep"""))

    #https://allmychanges.com/p/CSS/normalize.css/
    eq_('', process_vcs_message('3.0.2'))


def test_write_vcs_versions_bin_leaves_nulls_as_is():
    commits = [{'hash': 0, 'checkout': lambda: 2},
               {'hash': 1, 'checkout': lambda: None},
               {'hash': 2, 'checkout': lambda: 1},
               {'hash': 3, 'checkout': lambda: 1}]
    extract_version = lambda path: path

    write_vcs_versions_bin_helper(commits, extract_version)

    eq_(2,    commits[0]['version'])
    eq_(None, commits[1]['version'])
    eq_(1,    commits[2]['version'])
    eq_(1,    commits[3]['version'])
