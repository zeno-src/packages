#!/usr/bin/env python3
"""What the registry does with a filled-in "Publish a package" form.

The form is an issue. Its body has two answers under two headings:

    ### Repository

    https://github.com/someone/zeno-units

    ### Version

    v1.2.0

This script reads them, makes sure the person who filled the form in may
publish from that repository, and runs

    zeno registry accept . <repository> <version> --owner <their account>

which fetches the repository at that version, checks the package, and
writes its file in `index` and `index.json`. Then the script commits and
pushes what was written, and answers on the issue.

It is started by .github/workflows/publish.yml, which gives it the issue
in the variables ISSUE, BODY and LOGIN. Everything in BODY was typed by a
stranger: it is matched against two exact patterns here before any of it
goes near a command, and it only ever travels as one argument, never as
part of a command line that a shell reads.

A keeper of the registry can also start the workflow by hand, for a
package whose owner cannot use the form. Then there is no issue: the
answers come in REPOSITORY, VERSION and OWNER, the keeper stands for who
the owner is, and what would have been said on the issue is printed.
"""

import os
import re
import subprocess
import sys

# An address this form takes by itself: a repository on GitHub, by its
# owner and its name. Nothing else can stand in it: no `-` in front, no
# blank, no second address.
REPOSITORY = re.compile(r"https://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9._-]{1,100}?)(?:\.git)?/?")
# A version: the letter v and three numbers, each with no zero in front.
NUMBER = r"(?:0|[1-9][0-9]{0,8})"
VERSION = re.compile(rf"v{NUMBER}\.{NUMBER}\.{NUMBER}")
# A GitHub account.
ACCOUNT = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}")

DOCS = "https://github.com/zeno-src/zeno-lang/blob/main/docs/registry.md"


def answer_under(body, heading):
    """The text under `### heading` in the body of a form: its first line
    that is not empty."""
    lines = body.replace("\r\n", "\n").split("\n")
    for at, line in enumerate(lines):
        if line.strip() == f"### {heading}":
            for below in lines[at + 1:]:
                if below.startswith("### "):
                    break
                if below.strip():
                    return below.strip()
    return ""


def read_form(body):
    """The repository and the version a form asks for, or a sentence that
    says what is wrong with it."""
    repository = answer_under(body, "Repository")
    version = answer_under(body, "Version")
    found = REPOSITORY.fullmatch(repository)
    if not found:
        return None, (
            "The form takes a package that is on GitHub, by an address such as "
            "`https://github.com/someone/zeno-units`, and what stands under Repository is not one. "
            "A package that lives somewhere else can be in the registry too: say so in a comment here, "
            "and a keeper of the registry will look at it by hand."
        )
    if not VERSION.fullmatch(version):
        return None, (
            "What stands under Version is not a version. A version is a tag of the repository, "
            "written as the letter v and three numbers: `v1.2.0`."
        )
    return {"repository": repository.rstrip("/"), "owner": found.group(1), "version": version}, None


def may_publish(login, owner, is_public_member):
    """May the account `login` publish from a repository of `owner`?

    Yes if the repository is their own, or belongs to an organization
    that shows them as a member. That is all a registry can see from
    outside, and it is enough to stop somebody from publishing another
    person's work under a name they then own.
    """
    return login.lower() == owner.lower() or is_public_member(owner, login)


def quiet(command, **more):
    """Run a command, and give how it ended and what it printed."""
    ran = subprocess.run(command, capture_output=True, text=True, **more)
    return ran.returncode, (ran.stdout + ran.stderr).strip()


def is_public_member(organization, login):
    ended, _ = quiet(["gh", "api", "--silent", f"orgs/{organization}/public_members/{login}"])
    return ended == 0


def shown(text):
    """Text that came from outside, as a block that is shown letter for
    letter: nothing in it is taken for a link, a name to notify or the
    end of the block."""
    return "```\n" + text.replace("```", "'''") + "\n```"


def answer(issue, text, done):
    """Say `text` on the issue and close it: as done, or as not done.
    Somebody whose package was refused mends it and opens the issue
    again, which starts this script again.

    With no issue, the workflow was started by hand: the text is
    printed, and the run fails if the package was not taken."""
    if not issue:
        print(text)
        return 0 if done else 1
    subprocess.run(["gh", "issue", "comment", issue, "--body-file", "-"], input=text, text=True, check=True)
    reason = "completed" if done else "not planned"
    subprocess.run(["gh", "issue", "close", issue, "--reason", reason], check=True)
    return 0


def main():
    issue = os.environ.get("ISSUE", "")
    zeno = os.environ.get("ZENO", "zeno")
    if issue:
        body, login = os.environ["BODY"], os.environ["LOGIN"]
    else:
        # Started by hand: the three answers, made into the text of a form
        # so that they are read, and refused, by the same lines.
        body = f"### Repository\n\n{os.environ['REPOSITORY']}\n\n### Version\n\n{os.environ['VERSION']}\n"
        login = os.environ["OWNER"].strip()
        if not ACCOUNT.fullmatch(login):
            return answer(issue, "What stands under Owner is not the name of a GitHub account.", done=False)
    again = (
        "\n\nWhen that is put right, open this issue again with the button below (edit the form first, if it is "
        f"the form that was wrong), and the registry looks again. How publishing works: {DOCS}"
    )

    asked, wrong = read_form(body)
    if wrong:
        return answer(issue, wrong + again, done=False)
    repository, owner, version = asked["repository"], asked["owner"], asked["version"]

    if issue and not may_publish(login, owner, is_public_member):
        return answer(
            issue,
            f"This form was filled in by the account `{login}`, and the repository belongs to `{owner}`. "
            f"A package is published by the account that owns its repository, or by a member of the "
            f"organization that owns it whose membership is public "
            f"(https://github.com/orgs/{owner}/people shows it, and is where it is made public)." + again,
            done=False,
        )

    # Only `https` addresses are fetched, whatever a repository's own
    # files may say about where its parts are.
    limits = dict(os.environ, GIT_ALLOW_PROTOCOL="https")
    ended, said = quiet([zeno, "registry", "accept", ".", repository, version, "--owner", login], env=limits)
    if ended != 0:
        return answer(issue, f"The registry did not take `{repository}` at `{version}`:\n\n{shown(said)}{again}", done=False)

    # "Accepted units v1.2.0 (9f8e7d6) from https://..."
    name = said.split()[1]
    git = ["git", "-c", "user.name=github-actions[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com"]
    subprocess.run(["git", "add", "index", "index.json"], check=True)
    subprocess.run(git + ["commit", "--quiet", "-m", f"{name} {version} (#{issue})" if issue else f"{name} {version}"], check=True)
    # Somebody may have changed the registry by hand since this run began.
    subprocess.run(git + ["pull", "--quiet", "--rebase", "origin", "main"], check=True)
    subprocess.run(["git", "push", "--quiet", "origin", "HEAD:main"], check=True)

    return answer(
        issue,
        f"**`{name}` {version} is in the registry.**\n\n"
        f"A program gets it with this line in its `zeno.package`, and `zeno fetch`:\n\n"
        f"```\nneeds {name} at \"{version}\"\n```\n\n"
        f"It is listed at https://zeno-lang.org/packages/ and by `zeno search {name}`. "
        f"The name `{name}` is now yours: its next versions are published by `{login}`.",
        done=True,
    )


if __name__ == "__main__":
    sys.exit(main())
