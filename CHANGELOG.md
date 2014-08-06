0.5.1 (2014-08-06)
==================

* Links to badge and package versions were fixed.

0.5.0 (2014-08-06)
==================

This release includes a new changelogs processing pipeline, which now runs
in parallel to the old parser. We are keep eye on it's quality and performance
and will switch to it in the near future.

Also, there were some other changes:

* We've fixed how source suggest works for perl packages with two colons in name.
* OAuth token's field was made wider and now whole token is visible.
* Now our robot is able to recognize CVE security issues and to mark changelog's
  items as security, deprecation or backward incompatible. Look at the
  [Nginx's](http://allmychanges.com/u/svetlyak40wt/soft/nginx/#1.7.4) and
  [pip's](http://allmychanges.com/u/svetlyak40wt/python/pip/#1.6.0) changelogs
  to understand how it works.
* Also, missing values in 'Last update was' and 'Time to next update' were fixed.

0.4.0 (2014-06-28)
==================

Few cool feature, related to usability were added recently:

* Now service is able to guess source urls for packages in `perl`
  namespace.
* And we've implemented OAuth provider, allowing to write
  a third party tools and integrations.

Right now there is a simple interface to receive an OAuth token
and only one tool, implemented by myself — [command-line client](https://github.com/svetlyak40wt/allmychanges),
which have `import`, `export` and `add` commands.

Also other changes were introduced:

* Cleaner design (thanks to Maxim Sukharev a.k.a @smacker).
* A number of bugs were fixed.
	
0.3.0 (2014-06-03)
==================

More than month passed from the previous release and we'd like
to present a newer and better version of AllMyChanges.com.
A number of bugs were fixed and many improvements were made.
Actually, most of them were already tested in production because
we are using continuous delivery.

Here are most visible improvements, grouped by topics.

### Cool features

* Nice badge generator now shown on each package's page.
  It looks like this: ![](http://allmychanges.com/u/svetlyak40wt/web/allmychanges/badge)  
  and could be pasted into the `README.md` along with other
  badges from Travis and PyPi. This way viewers of you repository
  will be able to examine all changes in one glance without searching
  changelog in deeps of a source tree.

### Parsing improvements

* Now our robot is able to parse dates like this "May 21st 2014".
* Also, we now do our best in parsing changelogs with nonstandart formatting, like
  [Nginx's log](http://nginx.org/en/CHANGES). It was really hard to produce
  this [nicely formatted](http://allmychanges.com/u/svetlyak40wt/soft/nginx/) changelog from it.
* Version extraction for python packages was significantly improved.
  It is used when there is no human written changelog. In this case, our smart robot
  goes through VCS history and tries to reconstruct changelog from commit messages.
  Previously it worked only for python packages which use `setuptools` in their `setup.py`,
  but now we are using cool hack and version extraction works even for packages
  with `distutils`.
* Unreleased versions could be detected if there is a word `unreleased` in it's title.
  Here is an example: `Version 1.0.0 (unreleased)`.
  We'll understand that this version will be released in future and won't show it in the digest.

### User experience

* All new users have on default package in their digest - `web/allmychanges` as an example.
  And this package was added to the digest of all old users. If you want to receive news
  from the AllMyChanges.com, just leave this package in your digest.
* A [special page](http://allmychanges.com/account/settings/) was made where you is able to
  setup email and timezone. Please enter correct email to receive digest propertly.
* All digest email are sent around 9AM according to your timezone.
* Two improvements were made to digest editor:
  - Now it shows a latest discovered version near each packages and live update process
    started after a new package was added to the list.
  - For packages with namespace `python` we are trying to figure out it's source repository
    and show autocomplete if something was found. We are taking this data from PyPi.
    Probably for other landguages/ecosystems we could do this as well.


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
