from html.parser import HTMLParser

from wotd.core import LanguageProvider, SourceRequest, WOTDError, WordEntry, clean_text


class JapaneseWordParser(HTMLParser):
    """Extract the top-level Japanese word fields from Innovative Language HTML."""

    def __init__(self):
        super().__init__()
        self.fields = {
            "kanji": "",
            "kana": "",
            "romaji": "",
            "english_definition": "",
        }
        self._depth = 0
        self._word_section_depth = None
        self._capture_key = None
        self._capture_depth = None
        self._current = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = set(attrs_dict.get("class", "").split())

        if "wotd-widget-container-up" in classes and self._word_section_depth is None:
            self._word_section_depth = self._depth

        if self._word_section_depth is not None and self._capture_key is None:
            if "wotd-widget-sentence-main-space-text" in classes and not self.fields["kanji"]:
                self._capture_key = "kanji"
                self._capture_depth = self._depth
            elif "kana" in classes and not self.fields["kana"]:
                self._capture_key = "kana"
                self._capture_depth = self._depth
            elif "romaji" in classes and not self.fields["romaji"]:
                self._capture_key = "romaji"
                self._capture_depth = self._depth
            elif "english" in classes and not self.fields["english_definition"]:
                self._capture_key = "english_definition"
                self._capture_depth = self._depth

        self._depth += 1

    def handle_endtag(self, tag):
        self._depth -= 1

        if self._capture_key is not None and self._depth == self._capture_depth:
            text = clean_text("".join(self._current))
            if text:
                self.fields[self._capture_key] = text
            self._capture_key = None
            self._capture_depth = None
            self._current.clear()

        if self._word_section_depth is not None and self._depth == self._word_section_depth:
            self._word_section_depth = None

    def handle_data(self, data):
        if self._capture_key is not None:
            self._current.append(data)


def get_provider():
    return LanguageProvider(
        language="ja",
        source="Innovative Language",
        request=SourceRequest(
            url="https://www.innovativelanguage.com/widgets/wotd/large.php",
            data={
                "language": "Japanese",
                "type": "large",
            },
        ),
        parse=parse_japanese_entry,
    )


def parse_japanese_entry(page_bytes):
    html = page_bytes.decode("utf-8", errors="replace")
    parser = JapaneseWordParser()
    parser.feed(html)
    parser.close()

    kanji = parser.fields["kanji"]
    kana = parser.fields["kana"]
    romaji = parser.fields["romaji"]
    english_definition = parser.fields["english_definition"]

    if not all([kanji, kana, romaji, english_definition]):
        raise WOTDError("The Japanese source did not include all expected word fields.")

    return WordEntry(
        title=kanji,
        facts=[
            ("Kanji", kanji),
            ("Kana", kana),
            ("Romaji", romaji),
            ("English definition", english_definition),
        ],
        source="Innovative Language",
    )
