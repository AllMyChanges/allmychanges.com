1.5.0 (unreleased)
==================

## API Changes

* Now we return `changelog` field for tags.
* It is possible to filter versions by changelog's namespace, name and version number.
* Now changelogs can be filtered by keyword `id__in`.

## Fixes

* Fixed usage of symbols like `#` in namespace or project's name. Thanks to @hawkunsh for report about this problem.

1.4.0 (2016-03-21)
==================

## Some parser improvements

Some parser improvements were made to make it possible to parse
[Zabbix's release notes](https://allmychanges.com/p/soft/zabbix/):

* Now "Tune" page reports to the user which HTML pages were downloaded
  by recursive HTTP downloader.
* Now all `.php` files considered as having `html` markup.
* Now if there is a "search list" given by user, then files discovery
mechanism does not takes place.

## Other changes

* Fixed regression – text "NO FALLBACK DEFINED" in Slack's notifications.

1.3.0 (2016-03-20)
==================

## All About Slack

* Now Slack notifications are sent as attachments and large release notes are hidden under the "Show more..." link:
  ![](https://img-fotki.yandex.ru/get/69681/13558447.f/0_bc856_fbdbb295_L.png)
* Allowed whitespaces in a link description when preparing notification for Slack.
* Now images are presented as urls when posting notification to Slack. 

## Minor Changes

* It is possible to escaped slashes in `sed` changelog preprocessor's rules.
  This way, some items in the text can be replaced with urls. For example,
  this feature was used to link GitHub's and Launchpad's issue numbers
  to their actual pages for [python/lxml](https://allmychanges.com/p/python/lxml/).


1.2.1 (2016-03-17)
==================

* Fixed urls and bold text representation in Slack notifications:  
  ![](https://img-fotki.yandex.ru/get/67890/13558447.f/0_bc68a_c79b90d2_L.png)
* Fixed issue with updating projects where release dates are known.
* Fixed appstore and google play release notes headers.

1.2.0 (2016-03-14)
==================

* Algorithm which adds versions to the digest was significantly
improved. Now it shouldn't add many old versions for a new or
unpaused project.

* Now Slack and Webhook integrations can be tested by pressing
"Test" button on the [account's settings][account-settings] page.

* Also now we post full text of release notes to the Slack.

* Now we more precisely describe at
[account's settings][account-settings]
page, how often email notifications will be sent. Previously,
some users were confused because switching digests to 'Never' turns
off email notification completely and this wasn't obvious.


1.1.0 (2016-03-06)
==================

### Big feature

The main feature of this release, is a new way of collecting
changes for email digests. Previously there was an issue with
these digests. Some project maintainers keep a section with
unreleased version's description in the changelog. Old algorithm
discovered these versions but didn't sent them in an email when
this version has been released.

New algorithm, discovers the setuation, when known "unreleased"
version becomes "released" and includes it into a next digest
for every user who tracks the project.

### Second feature

Added support for one number versions, but these
should be prefixed with `v` or `r`, like `v15` and `r2015.01.02`.

This change made possible to parse release notes for
projects which use simple numbers for versioning.
Here are few examples:
  
* Kodi: [original][Kodi-original] -> [parsed][Kodi-parsed].
* FAR: [original][FAR-original] -> [parsed][FAR-parsed].
  
### Other changes

* Fixed error when comparing versions like 0.1.2-rc3.
* Allowed `sup` and `small` html tags in changelog markup.

1.0.1 (2016-02-21)
==================

* Fixed another place where snapshots are generated.

1.0.0 (2016-02-21)
==================

### Major changes

* Page with "Digest" was deprecated, now you'll see a link to [the page](https://allmychanges.com/account/track-list/) with a list of your tracked projects.

### Fixes

* Fixed parser's super power to build changelog from git's commits.
This is a huge improvement because some time ago, this feature was broken and we were unable to collect
changelogs for some projects. Now we are back in business :)
* Fixed `=====` in Google Play's release notes by using oneline format for markdown headers.
* Fixed our tool which makes a changelog's screenshot each time you share an URL to twitter or facebook.

### Minor changes

* Changed placeholder's text in the magic prompt.
* Added ability to view projects by id, using urls like `/p/54/`. But this is more for convenience during
log viewing and troubleshooting sessions.
* Added [changelogapp](https://github.com/samholmes1337/changelog) (nodejs command line utility) to a changelog [generators list](https://allmychanges.com/help/changelog-generators/).


### And more

We finally migrated to dockerized deployment. This opens following possibilities:

* it will be easier to scale in case if somebody suddenly will share a link at <https://www.producthunt.com>;
* it will be easier to create "enterprise" version of AllMyChanges which will be hosted by big companies in their intranets.
* it will be easier to setup development environment for a new team member. We are not hiring! But you can join the team if you want to build something useful for community.

In case, if you have any questions, write me to <mailto:sasha@allmychanges.com>.


0.31.0 (2016-01-16)
==================

### Major changes

New mechanism of package tuning and downloader selection.
Massive changes were made not only on the frontend, but
also at the backend.

### Minor

Now parser is able to process changelogs which are separated
to many files and where versions are in the filenames,
like in [openssh's release notes](http://www.openssh.com/txt/).
Here is the [result of parsing these release notes][openssh].

0.30.2 (2015-08-24)
===================

* Some face lifting was made. Thanks to @vovanbo for css diff!

0.30.1 (2015-08-04)
===================

* Use 'updated' date of atom feed if there is no 'published' date.
  This allowed us to process [Spring Boot's][spring-boot] and
  [Spring Framework's][spring-framework] changelogs.
* RSS integraion's field is 'readonly' now instead of 'disabled'. Thanks to @Splurov.
* Fixed Google Play's URLs processing when there are parameters other than 'id'.
  Thank again to @Splurov.

0.30.0 (2015-07-12)
===================

This release includes several important improvements:

* Better google play integration. Now it works even for apps
  which have different versions for different devices.
* Support for RSS/Atom feeds as a datasources was added.
  This allows to parse blogs' feed and now we are
  able to process [Ruby's][Ruby] and [Dropbox's][Dropbox]
  changelogs correctly.
* Javascript version of our packages catalogue was replaced
  with oldschool one. And now it show be more usable. Go and
  [check it yourself][catalogue].

By the way, if you were confused by "Add New" page's complexity,
than I have good news – next release will include a redesign
of this page. We are continually improve the service thanks to
your reports. Don't forget to sending us yor suggestions
[via email][support-email] or [gitter chat][gitter-chat].

0.29.0 (2015-06-30)
===================

Good news, everyone!
--------------------

We've added a new channel for reading your favorite release
notes. Now you can subscribe add a feed into your favorite
RSS reader.

<img src="https://c2.staticflickr.com/4/3323/3612905889_8fd2868286.jpg" width="500" height="298" alt="Good news, everyone! Futurama returns! by Bill Toenjes, on Flickr: https://www.flickr.com/photos/toomuchdew/3612905889">

To get you personal feed's URL, go to the [account settings][account-settings]
page and discover it in the "integrations" section.

Thanks to [Denis Gladkikh](https://github.com/outcoldman)
for pushing us into this direction.

0.28.0 (2015-06-16)
===================

First of all, I want to say "thank you" to all russian
developers who came from habrahabr to test our service.
Thank you guys, you've helped to find many issues and
to improve quality of the service.

Because of you reports we now, for example, we now
parse [OpenSSL's release notes][openssl] correctly.
To do this we have had to add a special preprocessing
engine which is like `sed` is able to prepare texts
before our robot will try to find there release notes.

Another changes
---------------

* We've fixed errors which prevented to parse
[FreeBSD's release notes][freebsd].
* Fixed an error in git commit messages parsing
which prevented processing of [Laravel Framework][laravel]
* Some other minor tweaks and fixes.

Again, thank you guys! Keep adding new projects
and reporting on issues!

0.27.0 (2015-05-31)
===================

Development is impossible without hooks
---------------------------------------

![Image by NevilleNel from Flickr](https://farm9.staticflickr.com/8705/16981764768_ac1c5d9770_z.jpg)

Did I say we implemented a generic web-hooks? Because we really did.
And now you can be not only receive notifications in Slack, but
do anything you want when a new version of a package is found.
Read [more about web-hooks][web-hooks] in our documentation.

To help you to automate your processes, we've prepared an
[example script](https://github.com/AllMyChanges/allmychanges-to-slack/blob/master/process.py)
which uses a python-processor to accept a web-hook and to post notification
further into different Slack channels and email, depending on package's
namespace.

Other things
------------

* Also, now we or processor is fixing header levels in GitHub Releases by replace
all `h1` headers with `h2` headers, all `h2` with `h3` and so on.
* Now package name is added as a hashtag when our robot
[@NewReleaseNotes][tw-new-release-notes] tweets about a new release.
* Annoying popups with tips wer disabled while we are implementing
a mechanism to remember which tips you already seen.
* We started experimenting with cal-heatmap javascript plugin
to show you your activity on the service. But it is not ready yet.

0.26.0 (2015-05-24)
===================

Many of you were begging us to make AllMyChanges work with
GitHub's releases API. And now this feature was implemented.

Among 700 packages in our database, only 500 are hosted at
the GitHub and 100 of them are using GitHub's Releases.
Now for all of these projects we can provide even better
release notes.

Here is piece of [libsass's][libsass] release notes collected
from git commit messages:

![](https://img-fotki.yandex.ru/get/9799/13558447.f/0_b4b95_eccbe71f_L.pn)

It is amazing how hand-written release notes are better:

![](https://img-fotki.yandex.ru/get/5103/13558447.f/0_b4b94_6c99f0d5_L.png)

And GitHub Releases are available for 20% of projects, hosted at the GitHub now.

Subscribe on them at AllMyChanges and we'll deliver new release right
into you mail box.

Other visible changes
---------------------

* Now we allow embedded video players in release notes.
* `<br>` tags were fixed  in sanitizer.
* Screenshots published into the twitter [@NewReleaseNotes][tw-new-release-notes]
  were improved.

0.25.0 (2015-05-18)
===================

This release includes two major features: "track list" page and "sharing like a pro".
First one will let you checkout which packages you are followed and sencond one
will make easier to share new releases to you friends on twitter.

Track List
----------

A lot of users were asking this feature. They wanted to see a list of
packages they are following on one page. Now this is possible.

Open this page by clicking this item in a dropdown menu:

![](https://img-fotki.yandex.ru/get/5606/13558447.f/0_b49c5_b956a514_M.png)

In a list you will see packages with their descriptions and latest version numbers.
All sorted alphabetically. If you have any ideas how to improve this page, please
[tweet to @allmychanges][tweet-us].

Share Like a Pro
----------------

Looking how often people are sharing pieces of release notes as a screenshots,
we decided to implement Twitter Cards specification to show parts of a changelog
as an image right in a twitter timeline.

Sadly, but this does not work. Twitter hides images from twitter cards by default
and you have to click on a tweet. So, we started a small research to find out a
best way to share fresh release notes with your friends.

And solution was found! Now, when our robot discovers a new version of a package,
she makes it's screenshot and posts it as a tweet to a [@NewReleaseNotes][tw-new-release-notes]
account.

For versions which were twitted this way, we show standart "Tweet" button on
web and email:

![](https://img-fotki.yandex.ru/get/3301/13558447.f/0_b49c9_10c736a3_L.png)

Clicking on this button will open a new window where you can
retweet the original post:

![](https://img-fotki.yandex.ru/get/6100/13558447.f/0_b49c7_b4541d65_L.png)

And you friends will see this retweet with a
screenshot of the changelog:

![](https://img-fotki.yandex.ru/get/4210/13558447.f/0_b49c6_c18ea39e_L.png)

If you don't like an idea to retweet, then just share a link to the changelog
and twitter will show a twitter card for it.

Finally
-------

Hey, are you still reading this? Go and test these new features!

0.24.1 (2015-05-14)
===================

* Login via GitHub button was fixed at popup appearing after clicking on "Follow" button. Closes issue #30. Thanks to Denis Gladkikh (@outcoldman) for reporting.
* Now tooltips are shown only after 15 seconds of inactivity at the page. More improvements are waiting in our roadmap.

0.24.0 (2015-05-11)
===================

Go Google Go!
-------------

Them main feature of this release is support for [Google Play](https://allmychanges.com/p/android/) URLs.
Find your favorite Android apps on Google Play, paste their URLs
right into the AllMyChanges's search bar and subscribe on the
release notes.

Changelog Roulette
------------------

Secondary change we would like to introduce is a better and smarter changelog suggestion on the front
page. Now it takes into account which packages did you track or skip in the past. There isn't machine
learning behind yet, but now it is much more interesting to flip through different packages, viewing
their latest release notes. Did I say you shoudl try it? No? Okay, [Go And Try It](https://allmychanges.com/)!

Other Changes
-------------

* Now we have a [FAQ page](https://allmychanges.com/help/faq/).
* Also, another help page was added – [Changelog Generators](https://allmychanges.com/help/changelog-generators/).
  It should help you to keep better release notes spending less time writing them.
* Few minor changes were introduced, like renaming of "Track" button into "Follow" button, etc..
* Also site now uses gorgeous [Intro.js](https://allmychanges.com/p/javascript/intro.js/) to show tooltips
  when you hang on a page for more than 15 seconds. We are thinking how to make this feature less annoying
  and more helpful. If you have any ideas, please [share them][support-email] with us.


0.23.0 (2015-04-22)
===================

This is release of minor improvements.

* Whole site went behind a HTTPS.
* Typography was fixed here and there.
* Buttons become more colorful and gradientish.
* Functions `amch:re.sub` and `amch:re.match` were available in XSLT transformations.
* Now we show spinner while waiting for autocomplete, because
  it is not optimized yet and sometimes takes really long to go through
  a billion of iOS apps, searching a term.
* Recursive http downloader was fixed to not add .html extensions to files
  with other content type.
* When anonymous track a package we show him (or her) a popup, explaining
  that to receive notifications he (or she) should login.
* And finally, now we show action buttons (report, track, etc.) on a
  sticky header along with version numbers.

0.22.0 (2015-04-05)
===================

This release includes two major features:

1. Design became responsive and more usable on devices with a small screen.
   Though not all pages are fixed yet, but frontpage and changelog os single
   package are looking good now on my iphone :)
2. Now XSL transformation could be applied to html pages before our
   robot will make attempt to find version descriptions there. This allows
   to fix weird HTML markup which brokes our data extraction algorithms.

   This powerful feature is accessable only to service creators. It allowed
   us to process release notes of [Minecraft][], [3D Engine Unity][Unity]
   and [Chrome][]. We hope to add more in the future.

   If you encounter a changelog which looks good on the web, but service is
   unable to handle it, [email us][support-email], and we'll be happy to help.

Also, there were a few minor changes:

* A bunch of SEO optimizations were introduced like micro formats support, meta tags,
last-modified caching, etc..
* Fixed date parsing for dates ended with dot, like "Released on Dec. 5, 2014."
* Added description of `amch` command line utility to the [tools page][tools].

0.21.0 (2015-04-02)
===================

Brand new autocomplete
----------------------

New autocomplete system was introduced.
Previously it worked only by our own database,
but now, when you are entering something into the
search bar, it also searches through over 1 million
apps from the Apple AppStore.

Very soon we'll add other sources for autocomplete,
such like PyPi, CPAN, NPM and GitHub.

Package descriptions
--------------------

From today, each package on AllMyChanges have new attribute
"description". It is optional, but we highly recomment to fill
it. For github projects we filled it automatically and are
planning to do this when new packages are added.

Filtering by attribute
----------------------

Now when tuning how changelog is parsed, you can
enter special filters into the "search list" textarea:

    [title=Release notes for \d.*]

This especially useful with `rechttp` downloader which
downloads bunch os html pages and tries to figure out which
parts of them are version descriptions. Using such
"attribute filters" you can help the parser to understand
which html headers are really contain version numbers.

Other changes
-------------

* Rechttp downloader now adds '.html' extension to urls without backslash at the end.
* Fixed error on a page for receiving [a token](http://allmychanges.com/account/token/) when
user come without login.
* Now we show number of trackers beside the "Track" button.
* Fixed a way how version numbers are compared when we are sorting them
(distutils's LooseVersion uses wrong algorithm).
* Fixed version parsing when there are upper-case letters in a version number 5.3.BETA-22.

0.20.1 (2015-03-16)
===================

* Don't send Slack notification when no new versions were found.

0.20.0 (2015-03-15)
===================

This release bring significant improvements in our
notification system. Now you could go into
your [account's settings](http://allmychanges.com/account/settings/) and to select
if you want to receive email digests daily or weekly.

Or, you could turn email notifications off and enable Slack
notification instead.

How to enable Slack notifications
---------------------------------

1. Go to you Slack account.
2. In channel's dropdown menu, choose "Add a service integration..."  
   ![](https://img-fotki.yandex.ru/get/6810/13558447.f/0_b36af_fdb87a97_L.png)
3. Next, filter all available integrations by "webhook" keyword.  
   ![](https://img-fotki.yandex.ru/get/5500/13558447.f/0_b36ae_4eb39439_L.png)
4. And select "Incoming WebHooks".
5. Choose a channel to which notification should be sent by AllMyChanges.
6. And push this huge "Add Incoming Webhook Integration" button :)
7. Finally, copy value from "Webhook URL" field into "Slack Url field at
   allmychanges's [account settings](http://allmychanges.com/account/settings/) page.


Other good news
---------------

Also, our downloader was improved and now it is able to fetch multiple pages.
This is required some tuning, but works pretty good. For example, whithout it
we weren't able to process release notes of some important projects, but here
they are:

* [PostgreSQL](http://allmychanges.com/p/soft/postgresql/)
* [Cloudera CDH](http://allmychanges.com/p/java/hadoop/)
* [Apache Spark](http://allmychanges.com/p/java/spark/)
* [Apache Kafka](http://allmychanges.com/p/java/kafka/)

Take look at the settings of these projects (push "Tune" button on their pages)
to understand how `rechttp` downloader works.


0.19.1 (2015-03-05)
===================

* Fix version parsing so that versions like `2.0-beta.6.7`,
`40.0.2214.73`, `v.1.0.3.2` and `2.0.1rc1` now parsed correctly. This made
possible to add new release notes of [Textmate](http://allmychanges.com/p/soft/textmate/),
[Chrome for iOS](http://allmychanges.com/p/ios/chrome/) and [suricata](http://allmychanges.com/p/security/suricata/).
* Nicer formatting for lines like:

        Bug #1184: pfring: cppcheck warnings
        Feature #1309: Lua support for Stats output

  parsed by plaintext parser.
* Also, plaintext parser now used `<br>` for textwrapping within paragraphs.
* Now we use `utf-8` as default encoding for files downloaded using `requests`. This fixes issues with unicode when server don't return encoding in the http headers.

0.19.0 (2015-03-03)
===================

This release brings an amazing feature.
Now you can track a changelog of any iOS application!

How to track iOS app's release notes?
-------------------------------------

It is very very easy. If you didn't find the app
in our [catalogue][] under `ios` namespace, then
search it in the AppStore and right click on app's
icon to open context menu. It could look like that:

![](https://img-fotki.yandex.ru/get/15567/13558447.f/0_b2c7f_9910ce74_M.png)

Or you could open drop down menu inder the apps icon:

![](https://img-fotki.yandex.ru/get/5110/13558447.f/0_b2c7e_55b034ce_L.png)

Select "Copy Link" menu item. Open [AllMyChanges.com](http://allmychanges.com)
and paste app's url into the search input at the top of the page.

After hitting the "Search" button you will see as service will process release notes
and show it as usual. And good news are -- it is trackable, and you even don't
have to install the app on your device!

P.S. -- if you are wondering if only latest Slack's release note was so verbose and nice,
go and discover their [previous release notes](http://allmychanges.com/p/ios/slack/).
I wish all app developers were like slack's developers not [like facebook's](http://allmychanges.com/p/ios/facebook/) :)))

0.18.2 (2015-03-01)
===================

* Plain text parser was fixed that way so now
  it is able to parse [nodejs][]'s changelog correctly.
  By the way, if you are interested in server-side
  javascript, then you could also track [iojs][]'s
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

[Packages catalogue][catalogue] is a browsable
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

[tools]: http://allmychanges.com/help/tools/
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
[Minecraft]: http://allmychanges.com/p/games/minecraft/
[Unity]: http://allmychanges.com/p/sdk/unity/
[Chrome]: http://allmychanges.com/p/soft/chrome/
[support-email]: mailto:support@allmychanges.com
[gitter-chat]: https://gitter.im/AllMyChanges/allmychanges.com
[tweet-us]: https://twitter.com/intent/tweet?text=@allmychanges%20hey,%20guys,%20
[tw-new-release-notes]: https://twitter.com/NewReleaseNotes
[libsass]: https://allmychanges.com/p/c%2B%2B/libsass/
[cal-heatmap]: https://github.com/kamisama/cal-heatmap
[web-hooks]: https://allmychanges.com/help/webhooks
[openssl]: https://allmychanges.com/p/security/openssl/
[freebsd]: https://allmychanges.com/p/os/freebsd/
[laravel]: https://allmychanges.com/p/php/laravel/
[account-settings]: https://allmychanges.com/account/settings/
[Ruby]: https://allmychanges.com/p/ruby/ruby/
[Dropbox]: https://allmychanges.com/p/soft/dropbox/
[catalogue]: http://allmychanges.com/p/
[spring-boot]: https://allmychanges.com/p/java/spring-boot/
[spring-framework]: https://allmychanges.com/p/java/spring-framework/
[openssh]: https://allmychanges.com/p/soft/openssh/
[Kodi-original]: http://kodi.wiki/view/Kodi_v16_(Jarvis)_changelog
[Kodi-parsed]: https://allmychanges.com/p/soft/Kodi/
[FAR-original]: http://svn.code.sf.net/p/farmanager/code/trunk/unicode_far/changelog
[FAR-parsed]: https://allmychanges.com/p/soft/FAR/
