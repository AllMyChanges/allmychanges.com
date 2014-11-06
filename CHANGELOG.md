0.10.1 (2014-11-06)
===================

* New account creation issue was fixed (thanks to Vasily Shmelev for report).
* A bunch of grammar mistakes were fixed on the front
  page (thanks to Yury Artemenko).

0.10.0 (2014-11-05)
===================

Today we released a new feauture. Now service's main
page don't redirect to http://allmychanges.com/digest/
anymore but shows 20 most recently updated packages
along with their versions.

That way it is really easy to track new packages.

0.9.2 (2014-10-30)
==================

* Fixed error when old versions appeared in the digest.
* Magic prompt's "Search" button was fixed.
* Now source downloader is selected automatically.
  URL prefixes like `http+` or `hg+` are obsolete now.

0.9.1 (2014-10-28)
==================

At the beginning of the project, we've had
a separate workflow when you come across interesting
project at the GitHub, click a bookmarklet and
allmychanges.com searches and displays project's
changelog.

This behaviour was broken because of refactoring,
but now it come back.

Go to the [/tools/](http://allmychanges.com/tools/) page
to install new bookmarklet!

0.9.0 (2014-10-27)
==================

This is a big release which completely changes a way how packages
are tracked. Previously, you have to open "Edit Digest" page and
to add packages one by one to the list. This interface
was completely replaced by the new one. Now each page contains
a magic search prompt. Try to enter there a package repository's
URL or just "namespace name" pair. The latter works only for `python`
and `perl` namespaces but will be extended to `npm` and `ruby gems` soon.

If allmychanges.com know nothing about entered source url, it will
offer you to add it and track. At the same time, it will try to fetch
changelog data and display them as soon as possible, allowing to
tune some crawler's parameters.

Another big change is new changelog parser which now works for everyone
by default. It is still immature, but we'll do our best to improve it's
quality. If you'll discover any errors or have ideas, please,
[write us an email][support-email].

Future plans
------------

* Improve new parser's quality.
* Simplify entering package description by automatic data gathering.
* Add an index page for logged in users. It will suggest packages to track.

Try new features and stay tuned!

0.8.3 (2014-09-14)
==================

Only two visible changes are introduced in this version.

* Digest editing page was renamed to 'Edit track list' and some links were made buttons.
* There was made a minor improvement in the way how changelog labels are rendered.
  This should fix they rendering in some mail clients, if don't, then contact us
  via [support@allmychanges.com](mail-to:support@allmychanges.com).

Another big feature which will come soon - global magic pony search. Stay tuned!

0.8.2 (2014-09-04)
==================

If you are writing changelogs for your own projects, please
keep dates simple and unambiguous. Something like YYYY-MM-DD
fill be ok. Teach your parents too ;-)

* Now for dates like 10.08.2014 parser takes first number as a day.
  This should fix issue with [django-taggit's](http://allmychanges.com/p/python/django-taggit/)
  changelog.

0.8.1 (2014-08-29)
==================

* Colored changelog item's labels in emails were fixed. Now emails should
  be much more readable. Thanks to [@bessarabov](https://twitter.com/bessarabov)
  for a report.
* Now all package urls are normalized upon save. This is most visible
  for GitHub hosted projects. For example, if you are submitting
  a url like `git@github.com:sass/sass.git`, it will be
  transformed to `https://github.com/sass/sass`.
* Now new parser only checks files if they have proper extension or
  it's filename looks like changelog.
* Fixed issue when new parser extracted version number from script html tags.

0.8.0 (2014-08-20)
==================

Now parser is able to group changelog items, extracted from
VCS history of Node.js packages. Horay! This means that we
could build a changelog for nodejs packages even if there
is no handwritten changelog!

There are some other changes too.

## Old (current) parser

* Fixed  parsing of dates like 'August 13th 2014'.
* Now VCS history parser ignores empty commit messages.

## New parser

* Scope where parser searches unreleased keywords was limited
  to first 300 symbols of version's description.
* Don't consider version number in case if it is preceeded by
  some symbols like backslash and other punctuation.
  Fixes cases with HTTP/1.1 parsed as a version number.
* Added ability to specify files and directories where to look
  for changelog data. These hints could help parser to recognize
  data in a vague situations.
* Now parser sanitizes HTML in his input files and escapes dangerous tags.

## Other changes

* Fixed issue when job queue was filled with numerous identical
  task which led to long intervals between package updates.
* Job's timeout was increased from 3 minutes to 10. This should
  help to process big repositories or extract logs from long VCS histories.

0.7.0 (2014-08-14)
==================

Both these changes are related to the new parser which is not available for wide audience. If you wish, [create an issue](https://github.com/AllMyChanges/allmychanges.com/issues) and we'll add you to the experiment.

* Added parser for plaintext files which are not looks like Markdown or Rst. This significantly improved perl packages' changelogs parsing.
* Fixed way how bullet changelogs are parsed (previously parser just ignored them). Now [python-redis's CHANGELOG](https://github.com/andymccurdy/redis-py/blob/master/CHANGES) is parsed correctly.


0.6.0 (2014-08-12)
==================

## Interface

* "Today" section of the digest was renamed to "Last 24 hours" because it is better describes an inner changelog discovery mechanics.
* Now service uses new fonts from TypeKit. More thin and clear. Please test it and [send us your suggestions](https://github.com/AllMyChanges/allmychanges.com/issues).

## Parser

* Fixed issue with perl/Mojolicious package where maintainer adds an empty unreleased versions into the changelog.
* Fixed error when parsing multiline changelog items. There was an issue with embedded newline characters and the way how these items were renderer. This is related to the new parser only.
* Fixed error during nodejs's changelog parsing, however it is still 
* Now parser is able to process dates like 2014/05/17.
* Also it've got an extended support for month abbreviations in parsed dates.
* Fixed way how dates parsed for perl's [boolean](https://github.com/ingydotnet/boolean-pm/blob/master/Changes) package.

## Other

* Now we think version is not release if there is 'not yet released' keyword in it'. I think we should put online documentation with description of all keywords and logic behind this mechanism.
* Now all code snippets for badges have a utm_source argument. Please, update you badges.

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

[support-email]: mailto:help@allmychanges.com
