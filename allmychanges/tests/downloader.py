import shutil
import time

from allmychanges.downloader import guess_downloader
from allmychanges.models import Changelog
from allmychanges.tests.utils import refresh
from nose.tools import eq_
from unittest.case import skip


@skip
def test_guesser():
    def guess(url):
        start = time.time()
        result = guess_downloader(url)
        print 'Guessed {0} for {1} in {2}'.format(
            result, url, time.time() - start)
        return result

    eq_('http', guess('https://github.com/lodash/lodash/wiki/Changelog'))
    eq_('git', guess('https://github.com/svetlyak40wt/django-fields'))
    eq_('git', guess('git://code.call-cc.org/chicken-core'))
    eq_('git', guess('http://git.haproxy.org/git/haproxy.git/'))
    eq_('git', guess('https://bitbucket.org/svetlyak40wt/test-git-repository'))
    eq_('git', guess('https://code.google.com/p/my-git-repository'))

    eq_('hg', guess('https://bitbucket.org/svetlyak40wt/test-hg-repository'))
    eq_('hg', guess('https://code.google.com/p/my-hg-repository'))

    eq_('http', guess('http://allmychanges.com/CHANGELOG.md'))
    eq_('http', guess('https://enterprise.github.com/releases'))

#    eq_('svn', guess('http://svn.code.sf.net/p/mathgl/code/mathgl-2x/'))
#    eq_('svn', guess('http://my-svn-repository-for-allmychanges.googlecode.com/svn/trunk/'))


def test_guesser_called_during_the_changelog_download():
    ch = Changelog.objects.create(source='https://github.com/svetlyak40wt/django-fields')
    eq_(None, ch.downloader)

    path = ch.download()
    if path:
        shutil.rmtree(path)

    ch = refresh(ch)
    eq_('git', ch.downloader)
