0.18.2 (2015-03-01)
===================

* Plain text parser was fixed that way so now
  it is able to parse [nodejs][]'s changelog correctly.
  By the way, if you are interested in server-side
  javascript, then you could also track [io.js][]'s
  changelog too.

0.18.1 (2015-02-28)
===================

* Source guesser was optimized to extract urls not only from
  html attributes but also from many other weird places.
  And, now it sorts results so that better matching come first.
* Also, guesser for python was slightly improved and now is
  able to find right repository urls for packages like django-extensions.
* Fixed issue with Django's 1.7.6 version which
  was parsed as released, but actually is "under development".
* Fixed error with unicode filenames in repository.
* URL validator was fixed to accept urls like `git@github...`
  and `hg+http://bitbucket...`.

0.18.0 (2015-02-08)
===================

The main feature of this release is a sticky navigation
bar for package's version.

Previously it was very hard to navigate through long
changelogs because large number of versions or because
their description was very long. Now this problem is solved
by special navigation bar which sticks to the top of the screen
and shows you a version number you are looking at and also
all other versions. And you can click on any version to
open it's description.

Other changes:

* Now service generated SVG badges instead of PNG.
  And they should look nice on retina displays.
* Keyword 'bugfixes' now highlighted.
* Now links to packages and their versions are blue in emailed
  digests.

And bugfixes (any software has bugs, right? :)):

* Fixed issue when version has a date but considered "unreleased"
  because a keyword in description.
* Fixed link from logo text to index page.

0.17.0 (2015-02-05)
===================

This release introduces significant changes in a way
how AllMyChanges stores and shows information about package's versions.

Previously, it tried to figure out where a list items in version
description, and store them separately on database level.
Also, our algorithm tagged these items with labels like "fix", "new"
"sec" and "dep". This approach produced nice results in very simple
cases and awful in relatively complex. For example it was unable
to handle nested lists and somitimes didn't work with complex html
changelogs.

Today we changed our processing pipeline, and will store
information about each version as whole text. Then it is processed
and some keywords are underlined to attract you attention to
bugfixes and security issues. We hope this algorithm will work
better with complex changelogs and will provide better user experience.

Right now not all packages have migrated to this new scheme, but all of them
will be converted sooner or later.

As usual, if you have any ideas how to improve the service, feel free to
drop a line via our [support email](mailto:support@allmychanges.com) or through
a feedback form available via click by "Report" button on package's page.

0.16.0 (2015-01-25)
===================

This version includes many bugfixes and improvements. The
most significant are: header's redesign, packages catalogue
and step by step guide after the first login.

Site header's redesign
----------------------

Now header includes a tree links to the main services functions.
Using these links, you could "add a new package", "navigate through
existing packages" and "view your digest".

Also, search input was completely rewrote in react.js and now should
work on every page even on the [angular's](http://allmychanges.com/p/javascript/angular.js/).
Now search results can contain three types of results: namespaces,
packages and urls found for given namespace and package's name on pypi.
In latter case, you could select this url to add it as a new package.

In other words, search become much more convinient now. Just go and
[try it yorself](http://allmychanges.com/)!

Packages catalogue
------------------

[Packages catalogue](http://allmychanges.com/catalogue/) is a browsable
directory of namespaces and packages known to the service.
This way you could discover interesting packages and track their changelogs.

Step by step guide
------------------

This is very important change because previously allmychanges was
too odd for a newcomer. It didn't tell him what to do after the registration.

Now service [tries to guide](http://allmychanges.com/first-steps/) user through setup and describes how to search
changelogs on the site and how to add new packages.

Other changes and fixes
-----------------------

* Now VCS parser is able to extract version information from git tags!
* Parser removes 'version bumps' from version descriptions extracted from VCS.
* When extracting changelog items from VCS history, newlines are replaced with html `<br>` tag.
* Version ordering at package's page was changed to more natural however sometimes still wrong.
* Now we use HTMLParser with 'utf-8' encoding when parsing html, this fixes processing unicode symbols in markdown changelogs.
* Now git history extractor processes branches properly.
* Fixed an error in VCS parser when last commit is a version bump.

0.15.0 (2014-12-24)
===================

This version contains many internal improvements and should
improve parsing quality. VCS changelog extractor was
significantly improved. Now it produces more correct results
and also it became 5 times faster. Few error in python
version extractor were fixed and now we should better group
commit messages for python projects. For example, previously
we did very poor job for [SleekXMPP][], but now are able
to show all latest versions correctly.

0.14.0 (2014-12-16)
===================

These changes should fix the [amch][], command line client to AllMyChanges.

* Now all source urls are normalized by API handles before changelog creation, update or search.
* Now changelogs could be filtered by source in API like `/v1/changelogs/?source=...`.
* Also, now API accepts urls starting with `git://...`.

0.13.3 (2014-12-05)
===================

* Better filtering of versions when there is version number in a filename
  and it is absent in the content.

0.13.2 (2014-12-04)
===================

* Fixed issue when parser ate some parts of text.
* Fixed way how changelogs are parsed when they are in a separate files where
  filenames include version number like in case of [Go][].
* Now algorithm ignores lines with more than 5 words when searching version numbers.

0.13.1 (2014-12-03)
===================

* Version description's typography was significantly improved.
  Now you can read [Django's changelog][django-1.7] and it won't hurt your eyes.
* Now preview's results are copied to an added package's changelog.
  This improves user experience, and seems more natural because
  you haven't to wait anymore.

0.13.0 (2014-11-30)
===================

An issue reporting was added for packages.
Use new button "Report" to open popup and fill the issue.
You will find this button near a package's title.

Please, write about any bugs, problems and inconsistencies, found
on site. This could be missing or wrong versions, bugs in a text or
date parsing, etc.

Right now this feature is in it's alfa stage. There is no ability
to communicate or even view issues you've filed. But we are
working on improving this feedback tool and will add comments
and email notifications in near future.

Leave your feedback, it is highly valuable for us.

0.12.5 (2014-11-27)
===================

* Fixed date parsing for cases like in
  [Synology's Disk Station's log](http://allmychanges.com/p/soft/synology-DS209j/),
  where version numbers like 4.2-3252 were parsed as dates.
* Fixed date parsing when date contains abbreviated month ending with dot like `Aug. 17, 2012`.
* Version parser's error was fixed. Previously it parsed `v3.0.0-pre` as `3.0.0`.
* Strip newlines and spaces from file section's titles when parsing html changelog.
  This fixes [lodash's changelog](https://github.com/lodash/lodash/wiki/Changelog) parsing.
* Fixed graphic badge generation for version with minus sign in them like `2.3-pre`.
* Now links to github's wiki or direct links to a raw files could be used as a changelog's source.

0.12.4 (2014-11-25)
===================

* Fixed issue when newly added packages were not updated regularly.

0.12.3 (2014-11-22)
===================

* Fixed error when file with .md extension could be considered having a reST format.
  This caused wrong changelog parsing for [Ansible][]
* Improved discovery of unreleased versions.
  Now we have a special checker which compares if latest version hasn't a release
  date but few  previous have. In this case, version without a date considered unreleased.
  This could be checked on the same project — [Ansible][]. It's maintainers add
  new feature and bugs description in a changelog and when they decide to ship a new
  version, they just specify a release date. Currently they are working on [1.8][ansible-1.8] version.
  
0.12.2 (2014-11-22)
===================

* Now VCS history extractor uses a new pipelined workflow and items' labels were fixed.

0.12.1 (2014-11-22)
===================

* Critical error was fixed, when all changelog's version were deleted before each update scheduling.

0.12.0 (2014-11-22)
===================

This release includes big refactoring of changelog and
preview update process. It is almost invisible for the end
users, except now you will see separate preview stages
during preview generation. I have ideas how to improve
it even more, but will leave this for a while.

Also, this release includes these minor changes:

* reST format recognizer was improved.
* And now reST parser removes field-list tables, so,
  for example, [Celery][celery-changelog]'s changelog looks much nicer now.
* Now changelog items's type labels are embedded into the HTML when changelog is parsed.
  This should improve changelog's rendering when items contains complex markup like
  paragraphs in the lists.
* Changelog styles was changed a little, to fix inner lists' margins.
* Also, search list saving on 'tune' page was fixed.

0.11.2 (2014-11-17)
===================

* Was fixed html changelogs type guesser and now [sbcl's][sbcl] changelog
  is parsed correctly.
* Fixed changelog items classification for [sbcl][] and [haproxy][].

0.11.1 (2014-11-11)
===================

* Our parser now works better with freak dates like `September 1st, 2014`
  and versions like `v2.0.0-beta.1`. This change will allow us
  to track [javascript/handlebars](http://allmychanges.com/p/javascript/handlebars),
  [javascript/meteor](http://allmychanges.com/p/javascript/meteor)
  and some other projects.
* Source type guesser was slightly improved and now is able to
  understand that GitHub Enterprise's
  [changelog](http://allmychanges.com/p/soft/github-enterprise) should be
  downloaded via HTTP, not via Git.
* Also, html changelog parsing was significantly improved
  and now abovementioned GitHub Entreprise's log looks
  relatively well.


0.11.0 (2014-11-11)
===================

Now downloader support branches for git repositories.
For example, [Celery][] uses separate branch to maintain
current stable version [3.1.x][celery-3.1]. And to gather
correct changelog, you have to specify correct repository
url: `https://github.com/celery/celery@3.1`. Pay attention
to the `@3.1` suffix. This way you specify a branch to be
checked out before our crawler will search and process
changelog.

Moreover, in this release:

* crawler become smarter when parsing documents in reST format.
* package view was fixed to not show versions created during preview.
* more grammatic fixes by Yuri  Artemenko.
* also, there is an internal improvement which allows us to track
  is our changelog parser was broken after latest release.

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
[Celery]: http://www.celeryproject.org/
[celery-3.1]: https://github.com/celery/celery/tree/3.1
[sbcl]: http://allmychanges.com/p/common-lisp/sbcl/
[haproxy]: http://allmychanges.com/p/soft/haproxy/
[celery-changelog]: http://allmychanges.com/p/python/celery/
[Ansible]: http://allmychanges.com/p/python/ansible/
[ansible-1.8]: http://allmychanges.com/p/python/ansible/#1.8
[django-1.7]: http://allmychanges.com/p/python/django/#1.7
[Go]: http://allmychanges.com/p/golang/go/
[amch]: https://github.com/svetlyak40wt/allmychanges
[SleekXMPP]: http://allmychanges.com/p/python/sleekxmpp/
[nodejs]: http://allmychanges.com/p/node/nodejs/
[iojs]: http://allmychanges.com/p/javascript/iojs/
