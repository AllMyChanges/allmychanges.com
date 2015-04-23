[Help](..) / FAQ
=================

<a class="anchor" href="#what-is-allmychanges" name="what-is-allmychanges">What is allmychanges.com?</a>
-------------------------

AllMyChanges is all about release notes you care about. It tracks them automatically and sends you updates via email or Slack.

<a class="anchor" href="#why-do-i-need-it" name="why-do-i-need-it">Why do you think I need it?
---------------------------

Well, if you don't care about security holes in your software. If you never break you apps because something
was changed in a third party library. Than you don't need it. Go away!

Are you still here? Why? Do you care about being on edge, being safe and using most recent features of numerous libraries, frameworks and SDKs? AllMyChanges will help you to automate release notes tracking. It is like a <strike>Google Reader</strike> Feedly for release notes and changelogs.

How does it work?
-----------------

You drop into a search field a link to a source were to search release notes. We do the rest. Actually, we don't, but our robot does.

If release notes could be found and extracted, we'll show them and you will be able to subscribe.

Actually many libraries, frameworks and apps already tracked by someone. Use search or catalogue to find them.

Did you say apps? Which apps?
-----------------------------

You can subscribe on any iOS app's release notes at allmychanges. Likes how Slack's release notes are written? Likes creativity of Trello's pr team? Track them at allmychanges and you never miss an update.

How to track some app's release notes?
--------------------------------------

First, try to search it by name in our search bar. If it is there, you are lucky, choose&track it!

If autocomplete unable to find the app, then find it in the AppStore, copy it's URL and paste into a search bar at allmychanges. Hit Enter. You have Enter on you keyboard, right? Hit it! And track. Don't forget to track!

Why do I have to login?
-----------------------

We need you email. I'm serious we need it. Not to sell it to spammers, but to be able to notify you about updates in release notes you've tracked.

How often I'll receive notifications about updates?
----------------------------------------------------

By default, we are sending a daily digest at 9am. If there were updates. But you could choose a period of week or turn email digests off at the settings page.

I want to receive updates ASAP. Is it possible?
-----------------------------------------------

Sure. We have Slack integration. Go and setup it!

Are you planning to add other integrations?
-------------------------------------------

Sure this is easy. Tell us about you needs. <a href="#feedback">Feedback form</a> is at the bottom of the page.

I don't want manually as everything from my requirements.txt, package.json, whatever.else. Is there a way to do this automatically?

Yes and no. Some popular libraries already in allmychanges' database. Other - don't. But to find release notes, our robot needs a link to source code, without it he (or may be she, we aren't sure yet :)) can't do the job.

But there is a tool to automate submitting packages. Using it, you could submit dependencies from any source like requirements.txt or package.json or anything else. This is a command line utility amch. It uses our secret undocumented API.

Do you have an API?
-------------------

Sure. But tsssss. It is a secret!

What kind of sources could you process?
---------------------------------------

Any link to any git or mercurial repository is ok. Not only GitHub, not only Bitbucket. Any public repository.

Or a link to an app in apple's AppStore.

Or URL of any html page containing version numbers in headers. I said, we could parse any release notes. Well almost any structured release notes.

Also it is possible to process multiple html pages, we have a special recursive downloader for that. But tuning it requires to be a 89 level Regex'n'XSL Mage. Just send us a link to a complex html release notes via <a href="#feedback">feedback form</a>, and we'll do the rest.

Agrhh! Explain, how it works?
-------------------------------------------------

As I said, there is a robot. He (or she, we really don't sure), does the job. It's like a magic. We feed it with coal, seems it's powered by steam. But it works! Really. I'm not joking. Go and try to drop an URL into a search field.

Ok, I tried. It is amazing! Now please, explain, what really happening behind the scene?
-------------------------------------------------------------------------------------------

Well, we have a bunch of downloaders, responsible for fetching sources from the link you gave us.

When sources are downloaded, we are trying to find handwritten release notes using file processors. These processors are able to process txt, markdown, restructured and html files. If something which looks like a version description was found, then these pieces are grouped and filtered to remove duplicates.

If processors were not able to find handwritten release notes, then we start another processor which tries to group release notes around versions. Right now it works only for git repositories and cases when there are tags with version numbers or for python and npm packages where we know how to extract version numbers.

Why don't you extract information from GitHub Releases API?
-----------------------------------------------------

Because it's is very few who really uses it. Tell us about some popular projects, writing their release notes at github, and we'll add this feature to our roadmap. Use <a href="#feedback">feedback form</a>.


<a name="feedback"></a>
Didn't find answer to your question? Ask it and we'll answer.
-------------------------------------------------------------

<div class="feedback-form-container" data-page="faq">Feedback form</div>

