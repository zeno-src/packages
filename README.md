# The Zeno package registry

This repository is where [Zeno](https://zeno-lang.org) finds a package
by its name. A program says in its `zeno.package`:

```
needs units at "v1.2.0"
```

and `zeno fetch` looks `units` up here, learns which git repository it
is and which commit of it is version 1.2.0, and fetches that commit.

**Browse the packages:** <https://zeno-lang.org/packages/>, or
`zeno search` and a word.

## What is here

The registry holds no packages. Each package stays in its author's own
git repository. What is here is one small file for each of them, in
[`index`](index), that says where it is:

```
package units
about "Lengths, masses and times that the checker keeps apart"
from "https://github.com/someone/zeno-units"
owner "someone"

version "v1.2.0" commit "9f8e7d6..." dated "2026-11-18"
```

[`index.json`](index.json) is the same list as one file, which the page
on zeno-lang.org reads. There is no server and there are no accounts
other than GitHub's: `zeno` reads this repository with git, as it reads
every package.

## Using a package

1. Find it: `zeno search filter`, or the page above.
2. Add the line it shows you to your program's `zeno.package`:
   `needs filters at "v1.0.0"`.
3. Run `zeno fetch` in the program's folder. The package, and the
   packages it needs, go into `packages/`, and `zeno.lock` records the
   exact commit of each.
4. `import filters` in your program.

A version is one exact thing. There are no ranges such as `^1.2`: the
version you wrote is the version you get.

## Publishing a package

A package is a git repository with a `zeno.package` at its top. To
publish a version of it:

1. Give `zeno.package` a line that says what the package is for:
   `about "Filters for noisy readings"`.
2. Commit, and tag the commit with its version: the letter v and three
   numbers.

   ```
   git tag v1.0.0
   git push origin main v1.0.0
   ```

3. Run `zeno publish` in the package's folder. It checks the package,
   and gives you the address of a form in this repository with the
   answers filled in.
4. Open that address, signed in to GitHub, and press the button. The
   registry fetches your repository at that tag, checks it again, adds
   it, and answers on the page, most often within a few minutes.

## The rules

- **A name** is 2 to 40 small letters, digits and `_`, and starts with
  a letter. It cannot be a word of the language or a module that comes
  with Zeno.
- **The first to publish a name owns it.** Later versions are taken
  only from the same repository, asked for by the same GitHub account.
- **You publish from a repository that is yours**: one that belongs to
  your account, or to an organization that shows you as a member.
- **A published version never changes.** The registry records the
  commit the tag named on the day it was published, and that commit is
  what everybody gets, even if the tag is moved afterwards. To change
  something, publish a new version.
- **A package may need other packages** by name, if they are in the
  registry already, or by the address of a git repository. It may not
  need a folder outside itself, which nobody else would have.
- **Every package has its own licence**, in its own repository. Read it
  before you use the package.

## Taking a package out, and other questions

Open an [issue](../../issues/new) that is not the form, and say what is
wrong: a package that does harm, a name that was taken to keep somebody
else from having it, a repository that has gone. A keeper of the
registry answers. A package is taken out by removing its file from
`index` and running `zeno registry index .`.

A security problem in Zeno itself goes to security@zeno-lang.org, as
[SECURITY.md](https://github.com/zeno-src/zeno-lang/blob/main/SECURITY.md)
says.

## How it works

- [`.github/ISSUE_TEMPLATE/publish.yml`](.github/ISSUE_TEMPLATE/publish.yml)
  is the form.
- [`.github/workflows/publish.yml`](.github/workflows/publish.yml) runs
  when the form is sent, and starts
  [`tools/publish.py`](tools/publish.py), which reads the form, checks
  who sent it, and runs `zeno registry accept`.
- `zeno registry accept` is part of Zeno itself. It fetches the
  repository at the tag, checks the package and writes its file. The
  walk through the code is
  [docs/registry.md](https://github.com/zeno-src/zeno-lang/blob/main/docs/registry.md)
  in the language's repository, and the reasons for each choice are in
  chapter 26 of its
  [decisions](https://github.com/zeno-src/zeno-lang/blob/main/docs/decisions.md).

## A registry of your own

A registry is any git repository. A company that wants its packages
kept inside can make one on its own server: `zeno registry accept` adds
a package to a clone of it, and a program names it in its
`zeno.package`:

```
registry "https://git.example.com/zeno-packages"
```
