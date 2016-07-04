==========
 WebHooks
==========

AllMyChanges is able to post notifications to any
WebHook. To setup this integration, go to the account
settings page and paste URL into the "WebHook's URL" field.

For processing web hooks we recommend you to use python-processor_.

Data Format
===========

AllMychanges will make a HTTP POST to the URL any time when
new versions for package are discovered. It provides you following
information:

.. code:: json

          {"namespace": "common-lisp",
           "name": "sbcl",
           "user_tags": [{"name": "some-environment", "version": "1.2.3"}],
           "versions": [
             {"released_at": null,
              "content": "<ul><li>minor incompatible change and ...",
              "number": "1.2.9",
              "discovered_at": "2015-03-22T18:12:00+00:00"},
             {"released_at": null,
              "content": "<ul><li>enhancement: better error and warning messages...",
              "number": "1.2.8",
              "discovered_at": "2015-02-20T18:12:00+00:00"}]}

Please note, there could be more than one version. And each version has two dates:
``released_at`` and ``discovered_at``. Release date could be empty if changelog's maintaners don't keep release dates in a changelog. If you are a maintainer of such changelog, please stop it!

Field ``discovered_at`` keeps a date when AllMyChanges bot discovered that version.

``Content`` field contains version's
description in a HTML format, that is the same content you see on the and
in email notifications.


.. _python-processor: https://python-processor.readthedocs.org
