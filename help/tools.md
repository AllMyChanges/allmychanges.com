[Help](..) / Tools
==================

Bookmarklet
-----------

Save this link to to your favorites or drag onto bookmarks toolbar:  
<a href="javascript:location.href='http://allmychanges.com/search/?q=' + encodeURIComponent(location.href)"
   style="text-decoration: none; border-bottom: 1px dotted;"
   onclick="return false">View Changelog</a>

Next, beeing on project's page click bookmarklet to view a release notes.

**Please, note**, that this bookmarklet doesn't work on GitHub's pages because it's developers
are security geeks. However it works nicely on [iTunes AppStore's](https://itunes.apple.com/us/genre/ios/id36?mt=8) pages
and at any other page containing html version of the changelog.

Command line utility
--------------------

There is also a [command line utility](https://github.com/svetlyak40wt/allmychanges) called `amch`, which is able
to import and export tracked packages. It uses generic data formats
like JSON, YAML or CSV and could be used with any other tools.

Here, for example, how you could upload to allmychanges all
dependencies from yours `requirements.txt` file:

    cat requirements.txt \
      | grep -v '^-e' \
      | sed -e 's/\([^=]\+\).*/python,\1/' \
            -e '1 i\namespace,name' \
      > data
    amch import --input data

First, with `cat`, `grep` and `sed` you prepare and input file `data` in CSV format.
And second – upload it to the service with `amch` command.

Read more about this tool at [it's documentation](https://github.com/svetlyak40wt/allmychanges#installation).
