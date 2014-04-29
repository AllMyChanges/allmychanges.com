0.2.1 (2014-04-21)
==================

* Fixed caching issue at digest page, when you've
  added a package, but digest seems not updated
  because of the cache.
* Fixed link to the package in digest email.
* Added cool feature — now our robot could download
  and parse any Markdown or ReST changelog.
  To force this behaviour, just add `http+` before
  the source URL.

0.2.0 (2014-04-18)
==================

* Now authentication via Twitter or GitHub was added.
* Now users are able to add separate packages to the list
  and receive email with digest of recent changes.

0.1.0 (2013-09-28)
==================

This app provides an easy way to collect changelogs of different
libraries. All information is gathered and presented in one format.
There are at least two possibilities to collect changelog data.

Firstly, allmychanges.com tries to find a plaintext file with
handwriten changelog. If it was found, we parse it and put to cache.
If there is no handwritten changelog, our robot applies all
his intelligence, to extract library's versions from VCS history and
tie each commit message to particular version. This is not very
accurate approach, but it is better than nothing.

First approach works with any kind of repository be it python, ruby or
even java, whereas as second approach needs more insights what is code
about. Right now, second approach only works with python modules, whose
setup.py uses setuptools.

There are plenty directions for approvement. Stay tuned.
