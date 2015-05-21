# Contributing

1.  Fork the project and clone your fork.

2.  Create a local feature branch:

        $ git checkout -b <branch>

3.  If adding a function `R.foo`, define it in __src/foo.js__ and include unit
    tests in __test/foo.js__. If adding an internal function `_foo`, define it
    in __src/internal/_foo.js__.

4.  Make one or more atomic commits. Each commit should have a descriptive
    commit message, wrapped at 72 characters. Do not commit changes to
    __dist/ramda.js__.

5.  Run `make test lint`, (or `grunt test`) and address any errors. Preferably,
    fix commits in place using `git rebase` or `git commit --amend` to make the
    changes easier to review and to keep the history tidy.

6.  Push to your fork:

        $ git push origin <branch>

7.  Open a pull request.

### Conventions

  - Do not use `Array.prototype.push`. Use `xs[idx] = x` or `xs[xs.length] = x`
    rather than `xs.push(x)`. See [#890][1] for links to related pull requests.


[1]: https://github.com/ramda/ramda/issues/890
