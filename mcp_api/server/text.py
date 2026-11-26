"""Plain-text helpers for Zenodo record fields."""

from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        self.parts.append(" ")

    def handle_endtag(self, tag):
        self.parts.append(" ")

    def handle_data(self, data):
        self.parts.append(data)


def strip_html(value: str) -> str:
    """Return the text of an HTML fragment (Zenodo descriptions are HTML)."""
    parser = _TextExtractor()
    parser.feed(value or "")
    parser.close()
    return " ".join("".join(parser.parts).split())
