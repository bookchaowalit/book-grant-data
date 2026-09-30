"""Drift guard: text hidden from readers must not satisfy source markers."""
import unittest

from book_grant_data.capture import Text


def visible(html):
    parser = Text()
    parser.feed(html)
    return " ".join(" ".join(parser.parts).split())


class TextExtractionTests(unittest.TestCase):
    def test_hidden_containers_are_ignored(self):
        for tag in ("script", "style", "noscript", "svg"):
            with self.subTest(tag=tag):
                html = f"<p>Access denied</p><{tag}>official program marker</{tag}><p>retry</p>"
                self.assertEqual(visible(html), "Access denied retry")

    def test_nested_and_unbalanced_hidden_tags_recover(self):
        self.assertEqual(visible("<svg><title>x</title><svg>y</svg>z</svg><p>shown</p>"), "shown")
        self.assertEqual(visible("</noscript><p>shown</p>"), "shown")


if __name__ == "__main__":
    unittest.main()
