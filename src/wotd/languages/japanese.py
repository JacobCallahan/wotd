from html.parser import HTMLParser
import xml.etree.ElementTree as ET

from wotd.core import LanguageProvider, SourceRequest, WOTDError, WordEntry, clean_text

DEFAULT_LEVEL = "n5"
JLPT_LEVELS = ("n1", "n2", "n3", "n4", "n5")


class JapaneseDescriptionParser(HTMLParser):
    """Extract paragraph blocks from the Japanese RSS description HTML."""

    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self._current_style = None
        self._current = []

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self._flush()
            self._current_style = dict(attrs).get("style", "")
        elif tag == "br":
            self._current.append("\n")

    def handle_endtag(self, tag):
        if tag == "p":
            self._flush()
            self._current_style = None

    def handle_data(self, data):
        self._current.append(data)

    def _flush(self):
        text = "".join(self._current)
        cleaned_lines = [clean_text(line) for line in text.splitlines()]
        cleaned_lines = [line for line in cleaned_lines if line]
        if self._current_style is not None or cleaned_lines:
            self.paragraphs.append(
                {
                    "style": self._current_style or "",
                    "lines": cleaned_lines,
                }
            )
        self._current.clear()

    def close(self):
        super().close()
        self._flush()


def get_provider():
    return LanguageProvider(
        language="ja",
        source="Kanji of the Day",
        build_request=build_request,
        parse=parse_japanese_entry,
        variants=JLPT_LEVELS,
        default_variant=DEFAULT_LEVEL,
    )


def build_request(variant):
    level = variant or DEFAULT_LEVEL
    if level not in JLPT_LEVELS:
        raise WOTDError(f"Unsupported Japanese level '{level}'.")
    return SourceRequest(url=f"https://kotd.dperkins.org/jlpt.{level}.xml")


def parse_japanese_entry(feed_bytes, variant):
    try:
        root = ET.fromstring(feed_bytes)
    except ET.ParseError as exc:
        raise WOTDError(f"Could not parse Japanese RSS XML: {exc}.") from exc

    channel = root.find("channel")
    if channel is None:
        raise WOTDError("Japanese RSS feed is missing a channel element.")

    item = channel.find("item")
    if item is None:
        raise WOTDError("Japanese RSS feed did not contain any items.")

    description_html = item.findtext("description", default="")
    parser = JapaneseDescriptionParser()
    parser.feed(description_html)
    parser.close()

    paragraphs = parser.paragraphs
    if not paragraphs:
        raise WOTDError("The Japanese source did not include the expected kanji fields.")

    kanji = _first_line_matching(paragraphs, "font-size: 500%")
    english_definition = _first_line_matching(paragraphs, "color: green")
    on_reading = _first_line_matching(paragraphs, "color: orange")
    kun_reading = _first_line_matching(paragraphs, "color: red")
    examples = _join_lines_matching(paragraphs, "")

    kana = " / ".join(reading for reading in (on_reading, kun_reading) if reading)
    romaji = " / ".join(kana_to_romaji(reading) for reading in (on_reading, kun_reading) if reading)

    if not all([kanji, kana, romaji, english_definition]):
        raise WOTDError("The Japanese source did not include all expected word fields.")

    level = (variant or DEFAULT_LEVEL).upper()
    return WordEntry(
        title=kanji,
        facts=[
            ("Kanji", kanji),
            ("Kana", kana),
            ("Romaji", romaji),
            ("English definition", english_definition),
            ("Level", level),
        ],
        description=examples,
        description_label="Examples",
        source=f"Kanji of the Day ({level})",
    )


def _first_line_matching(paragraphs, style_fragment):
    for paragraph in paragraphs:
        if style_fragment in paragraph["style"] and paragraph["lines"]:
            return paragraph["lines"][0]
    return ""


def _join_lines_matching(paragraphs, style_fragment):
    for paragraph in paragraphs:
        if style_fragment == paragraph["style"] and paragraph["lines"]:
            return "\n".join(paragraph["lines"])
    return ""


def kana_to_romaji(text):
    normalized = text.strip().replace(".", "")
    if not normalized:
        return ""

    result = []
    index = 0
    geminate = False
    while index < len(normalized):
        char = normalized[index]

        if char in {" ", "/", ",", "(", ")", "-"}:
            result.append(char)
            index += 1
            continue

        if char in {"っ", "ッ"}:
            geminate = True
            index += 1
            continue

        if char == "ー":
            if result:
                result[-1] = extend_vowel(result[-1])
            index += 1
            continue

        pair = normalized[index : index + 2]
        syllable = DIGRAPHS.get(pair)
        if syllable is not None:
            index += 2
        else:
            syllable = KANA_TO_ROMAJI.get(char, char)
            index += 1

        if geminate and syllable:
            syllable = syllable[0] + syllable
            geminate = False

        result.append(syllable)

    return "".join(result)


def extend_vowel(previous):
    for vowel in reversed(previous):
        if vowel in "aeiou":
            return previous + vowel
    return previous


DIGRAPHS = {
    "きゃ": "kya",
    "きゅ": "kyu",
    "きょ": "kyo",
    "しゃ": "sha",
    "しゅ": "shu",
    "しょ": "sho",
    "ちゃ": "cha",
    "ちゅ": "chu",
    "ちょ": "cho",
    "にゃ": "nya",
    "にゅ": "nyu",
    "にょ": "nyo",
    "ひゃ": "hya",
    "ひゅ": "hyu",
    "ひょ": "hyo",
    "みゃ": "mya",
    "みゅ": "myu",
    "みょ": "myo",
    "りゃ": "rya",
    "りゅ": "ryu",
    "りょ": "ryo",
    "ぎゃ": "gya",
    "ぎゅ": "gyu",
    "ぎょ": "gyo",
    "じゃ": "ja",
    "じゅ": "ju",
    "じょ": "jo",
    "びゃ": "bya",
    "びゅ": "byu",
    "びょ": "byo",
    "ぴゃ": "pya",
    "ぴゅ": "pyu",
    "ぴょ": "pyo",
    "キャ": "kya",
    "キュ": "kyu",
    "キョ": "kyo",
    "シャ": "sha",
    "シュ": "shu",
    "ショ": "sho",
    "チャ": "cha",
    "チュ": "chu",
    "チョ": "cho",
    "ニャ": "nya",
    "ニュ": "nyu",
    "ニョ": "nyo",
    "ヒャ": "hya",
    "ヒュ": "hyu",
    "ヒョ": "hyo",
    "ミャ": "mya",
    "ミュ": "myu",
    "ミョ": "myo",
    "リャ": "rya",
    "リュ": "ryu",
    "リョ": "ryo",
    "ギャ": "gya",
    "ギュ": "gyu",
    "ギョ": "gyo",
    "ジャ": "ja",
    "ジュ": "ju",
    "ジョ": "jo",
    "ビャ": "bya",
    "ビュ": "byu",
    "ビョ": "byo",
    "ピャ": "pya",
    "ピュ": "pyu",
    "ピョ": "pyo",
}

KANA_TO_ROMAJI = {
    "あ": "a",
    "い": "i",
    "う": "u",
    "え": "e",
    "お": "o",
    "か": "ka",
    "き": "ki",
    "く": "ku",
    "け": "ke",
    "こ": "ko",
    "さ": "sa",
    "し": "shi",
    "す": "su",
    "せ": "se",
    "そ": "so",
    "た": "ta",
    "ち": "chi",
    "つ": "tsu",
    "て": "te",
    "と": "to",
    "な": "na",
    "に": "ni",
    "ぬ": "nu",
    "ね": "ne",
    "の": "no",
    "は": "ha",
    "ひ": "hi",
    "ふ": "fu",
    "へ": "he",
    "ほ": "ho",
    "ま": "ma",
    "み": "mi",
    "む": "mu",
    "め": "me",
    "も": "mo",
    "や": "ya",
    "ゆ": "yu",
    "よ": "yo",
    "ら": "ra",
    "り": "ri",
    "る": "ru",
    "れ": "re",
    "ろ": "ro",
    "わ": "wa",
    "を": "o",
    "ん": "n",
    "が": "ga",
    "ぎ": "gi",
    "ぐ": "gu",
    "げ": "ge",
    "ご": "go",
    "ざ": "za",
    "じ": "ji",
    "ず": "zu",
    "ぜ": "ze",
    "ぞ": "zo",
    "だ": "da",
    "ぢ": "ji",
    "づ": "zu",
    "で": "de",
    "ど": "do",
    "ば": "ba",
    "び": "bi",
    "ぶ": "bu",
    "べ": "be",
    "ぼ": "bo",
    "ぱ": "pa",
    "ぴ": "pi",
    "ぷ": "pu",
    "ぺ": "pe",
    "ぽ": "po",
    "ぁ": "a",
    "ぃ": "i",
    "ぅ": "u",
    "ぇ": "e",
    "ぉ": "o",
    "ア": "a",
    "イ": "i",
    "ウ": "u",
    "エ": "e",
    "オ": "o",
    "カ": "ka",
    "キ": "ki",
    "ク": "ku",
    "ケ": "ke",
    "コ": "ko",
    "サ": "sa",
    "シ": "shi",
    "ス": "su",
    "セ": "se",
    "ソ": "so",
    "タ": "ta",
    "チ": "chi",
    "ツ": "tsu",
    "テ": "te",
    "ト": "to",
    "ナ": "na",
    "ニ": "ni",
    "ヌ": "nu",
    "ネ": "ne",
    "ノ": "no",
    "ハ": "ha",
    "ヒ": "hi",
    "フ": "fu",
    "ヘ": "he",
    "ホ": "ho",
    "マ": "ma",
    "ミ": "mi",
    "ム": "mu",
    "メ": "me",
    "モ": "mo",
    "ヤ": "ya",
    "ユ": "yu",
    "ヨ": "yo",
    "ラ": "ra",
    "リ": "ri",
    "ル": "ru",
    "レ": "re",
    "ロ": "ro",
    "ワ": "wa",
    "ヲ": "o",
    "ン": "n",
    "ガ": "ga",
    "ギ": "gi",
    "グ": "gu",
    "ゲ": "ge",
    "ゴ": "go",
    "ザ": "za",
    "ジ": "ji",
    "ズ": "zu",
    "ゼ": "ze",
    "ゾ": "zo",
    "ダ": "da",
    "ヂ": "ji",
    "ヅ": "zu",
    "デ": "de",
    "ド": "do",
    "バ": "ba",
    "ビ": "bi",
    "ブ": "bu",
    "ベ": "be",
    "ボ": "bo",
    "パ": "pa",
    "ピ": "pi",
    "プ": "pu",
    "ペ": "pe",
    "ポ": "po",
    "ァ": "a",
    "ィ": "i",
    "ゥ": "u",
    "ェ": "e",
    "ォ": "o",
}
