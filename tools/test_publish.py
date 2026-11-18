"""Tests for publish.py: `python3 -m unittest discover tools`."""

import unittest

from publish import may_publish, read_form, shown


def form(repository, version):
    return f"### Repository\n\n{repository}\n\n### Version\n\n{version}\n"


class ReadForm(unittest.TestCase):
    def test_a_form_is_read(self):
        asked, wrong = read_form(form("https://github.com/someone/zeno-units", "v1.2.0"))
        self.assertIsNone(wrong)
        self.assertEqual(asked, {"repository": "https://github.com/someone/zeno-units", "owner": "someone", "version": "v1.2.0"})

    def test_the_endings_that_change_nothing(self):
        for written in ["https://github.com/someone/zeno-units.git", "https://github.com/someone/zeno-units/", "  https://github.com/someone/zeno-units  "]:
            asked, wrong = read_form(form(written, "v0.0.1"))
            self.assertIsNone(wrong, written)
            self.assertEqual(asked["owner"], "someone")

    def test_windows_line_ends(self):
        asked, _ = read_form(form("https://github.com/a/b", "v1.0.0").replace("\n", "\r\n"))
        self.assertEqual(asked["version"], "v1.0.0")

    def test_what_is_not_a_repository_on_github(self):
        for written in [
            "",
            "_No response_",
            "github.com/someone/units",
            "http://github.com/someone/units",
            "https://gitlab.com/someone/units",
            "https://github.com/someone",
            "https://github.com/someone/units/tree/main",
            "https://github.com/someone/units v1.0.0",
            "https://github.com/someone/units;rm -rf .",
            "https://github.com/-someone/units",
            "--upload-pack=x",
            "https://user:secret@github.com/someone/units",
        ]:
            asked, wrong = read_form(form(written, "v1.0.0"))
            self.assertIsNone(asked, written)
            self.assertIn("under Repository is not one", wrong)

    def test_what_is_not_a_version(self):
        for written in ["", "1.2.0", "v1.2", "v1.02.0", "main", "v1.2.0-rc1", "v1.2.0 --force", "$(id)"]:
            asked, wrong = read_form(form("https://github.com/someone/units", written))
            self.assertIsNone(asked, written)
            self.assertIn("is not a version", wrong)

    def test_an_answer_cannot_bring_a_heading_of_its_own(self):
        # Whatever is typed into the first box stays in the first box.
        body = "### Repository\n\nhttps://github.com/eve/units\n\n### Version\n\nv1.0.0\n\n### Repository\n\nhttps://github.com/ada/units\n"
        asked, _ = read_form(body)
        self.assertEqual(asked["owner"], "eve")


class MayPublish(unittest.TestCase):
    def test_the_owner_of_the_repository(self):
        nobody = lambda organization, login: False
        self.assertTrue(may_publish("someone", "someone", nobody))
        self.assertTrue(may_publish("SomeOne", "someone", nobody))
        self.assertFalse(may_publish("eve", "someone", nobody))

    def test_a_public_member_of_the_organization(self):
        members = lambda organization, login: (organization, login) == ("zeno-src", "ada")
        self.assertTrue(may_publish("ada", "zeno-src", members))
        self.assertFalse(may_publish("eve", "zeno-src", members))


class Shown(unittest.TestCase):
    def test_a_message_cannot_end_its_block(self):
        self.assertEqual(shown("a ``` b"), "```\na ''' b\n```")


if __name__ == "__main__":
    unittest.main()
