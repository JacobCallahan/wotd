from html.parser import HTMLParser
import xml.etree.ElementTree as ET

from wotd.core import LanguageProvider, SourceRequest, WOTDError, WordEntry, clean_text

MERRIAM_NAMESPACE = {"merriam": "https://www.merriam-webster.com/word-of-the-day"}


class DescriptionParagraphParser(HTMLParser):
    """Collect paragraph-like text from the feed's HTML description."""

    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self._current = []

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self._flush()
        elif tag == "br":
            self._current.append("\n")

    def handle_endtag(self, tag):
        if tag == "p":
            self._flush()

    def handle_data(self, data):
        self._current.append(data)

    def _flush(self):
        text = clean_text("".join(self._current))
        if text:
            self.paragraphs.append(text)
        self._current.clear()

    def close(self):
        super().close()
        self._flush()


def get_provider():
    return LanguageProvider(
        language="en",
        source="Merriam-Webster",
        request=SourceRequest(url="https://www.merriam-webster.com/wotd/feed/rss2"),
        parse=parse_latest_item,
    )


def parse_latest_item(feed_bytes):
    try:
        root = ET.fromstring(feed_bytes)
    except ET.ParseError as exc:
        raise WOTDError(f"Could not parse RSS XML: {exc}.") from exc

    channel = root.find("channel")
    if channel is None:
        raise WOTDError("RSS feed is missing a channel element.")

    item = channel.find("item")
    if item is None:
        raise WOTDError("RSS feed did not contain any items.")

    word = clean_text(item.findtext("title", default=""))
    if not word:
        raise WOTDError("The newest feed item is missing its word title.")

    definitions = extract_definitions(item, word)
    if not definitions:
        raise WOTDError(f"The newest feed item for '{word}' did not include any definitions.")

    return WordEntry(
        title=word,
        definitions=definitions,
        description=extract_description(item, word),
        source="Merriam-Webster",
    )


def extract_definitions(item, word):
    shortdefs = [
        clean_text(shortdef.text or "")
        for shortdef in item.findall("merriam:shortdef", MERRIAM_NAMESPACE)
        if clean_text(shortdef.text or "")
    ]
    if shortdefs:
        return shortdefs

    description = item.findtext("description", default="")
    return _description_paragraphs(description, word)


def extract_description(item, word):
    description = item.findtext("description", default="")
    return "\n\n".join(_description_paragraphs(description, word))


def _description_paragraphs(description_html, word):
    if not description_html.strip():
        return []

    parser = DescriptionParagraphParser()
    parser.feed(description_html)
    parser.close()

    kept = []
    for paragraph in parser.paragraphs:
        lowered = paragraph.lower()
        if lowered.startswith("merriam-webster's word of the day"):
            continue
        if "see the entry" in lowered:
            continue
        if lowered.startswith("examples:") or lowered.startswith("did you know?"):
            break
        if paragraph.startswith("//"):
            continue
        kept.append(paragraph)

    if kept and _looks_like_headword_line(kept[0], word):
        kept = kept[1:]

    return kept


def _looks_like_headword_line(text, word):
    lowered = text.lower()
    return word.lower() in lowered and any(
        marker in lowered for marker in ("\\", " noun", " verb", " adjective", " adverb")
    )
